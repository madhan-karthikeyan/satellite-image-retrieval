"""Image embedding module using RemoteCLIP with Test-Time Augmentation."""

import os
from pathlib import Path
from typing import Optional, Callable
import torch
import torch.nn.functional as F
from PIL import Image, ImageOps, ImageEnhance
from huggingface_hub import hf_hub_download
import open_clip


def get_project_root() -> Path:
    """Get the project root directory (parent of ml-service)."""
    return Path(__file__).parent.parent


class TTATransform:
    """Test-Time Augmentation transforms for more robust embeddings."""

    def __init__(self, base_transform: Callable, sizes: list[int] = None):
        self.base_transform = base_transform
        self.sizes = sizes or [224]

    def __call__(self, image: Image.Image) -> list[torch.Tensor]:
        transforms = []

        for size in self.sizes:
            resized = image.resize((size, size), Image.BILINEAR)
            transforms.append(self.base_transform(resized))

        return transforms


class Embedder:
    """RemoteCLIP-based image embedder with TTA support."""

    def __init__(
        self,
        device: Optional[str] = None,
        use_tta: bool = True,
        tta_augmentations: int = 8
    ):
        """Initialize embedder with RemoteCLIP model.

        Args:
            device: Device to use ('cuda', 'cpu', or None for auto-detect)
            use_tta: Enable Test-Time Augmentation for more robust embeddings
            tta_augmentations: Number of TTA augmentations (8 = full set, 4 = basic)
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.use_tta = use_tta
        self.tta_augmentations = min(max(tta_augmentations, 1), 8)

        project_root = get_project_root()
        checkpoint_dir = project_root / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        print("Downloading RemoteCLIP-ViT-L-14 checkpoint...")
        checkpoint_path = hf_hub_download(
            "chendelong/RemoteCLIP",
            "RemoteCLIP-ViT-L-14.pt",
            cache_dir=str(checkpoint_dir)
        )
        print(f"Checkpoint downloaded to: {checkpoint_path}")

        print("Loading RemoteCLIP model...")
        model, _, preprocess_fn = open_clip.create_model_and_transforms(
            "ViT-L-14",
            pretrained="openai"
        )

        ckpt = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        if hasattr(ckpt, 'state_dict'):
            ckpt = ckpt.state_dict()
        result = model.load_state_dict(ckpt, strict=False)
        print(f"Loaded checkpoint: {result}")

        model = model.to(self.device).eval()

        self.model = model
        self._preprocess_fn = preprocess_fn

    def _apply_tta_augmentations(self, image: Image.Image) -> list[Image.Image]:
        """Generate TTA augmented views of the image."""
        augmented = []

        augmented.append(image.copy())
        augmented.append(ImageOps.flip(image))
        augmented.append(ImageOps.mirror(image))
        augmented.append(ImageOps.grayscale(image).convert("RGB"))

        rotations = [90, 180, 270] if self.tta_augmentations >= 8 else [180]
        for angle in rotations:
            augmented.append(image.rotate(angle, expand=True))

        if self.tta_augmentations >= 4:
            brightnesses = [0.9, 1.1]
            for brightness in brightnesses:
                enhanced = ImageOps.autocontrast(image)
                enhanced = ImageEnhance.Brightness(enhanced).enhance(brightness)
                augmented.append(enhanced)

        return augmented[:self.tta_augmentations]

    def preprocess(self, image: Image.Image) -> torch.Tensor:
        """Preprocess image for RemoteCLIP.

        Args:
            image: PIL Image (224x224 expected)

        Returns:
            Preprocessed pixel values tensor with batch dimension
        """
        processed = self._preprocess_fn(image)
        processed = processed.unsqueeze(0)
        return processed.to(self.device)

    def embed(self, pixel_values: torch.Tensor) -> list[float]:
        """Generate embedding from preprocessed image.

        Args:
            pixel_values: Preprocessed image tensor

        Returns:
            L2-normalized embedding vector as list of floats
        """
        with torch.no_grad():
            image_features = self.model.encode_image(pixel_values)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            embedding = image_features.squeeze().cpu().tolist()

        return embedding

    def embed_batch(self, pixel_values: torch.Tensor) -> list[list[float]]:
        """Generate embeddings from a batch of preprocessed images.

        Args:
            pixel_values: Batch of preprocessed images [B, C, H, W]

        Returns:
            List of L2-normalized embedding vectors
        """
        with torch.no_grad():
            image_features = self.model.encode_image(pixel_values)
            image_features = F.normalize(image_features, dim=-1)
            embeddings = image_features.cpu().tolist()

        return embeddings

    def embed_with_tta(self, image: Image.Image) -> list[float]:
        """Generate embedding with Test-Time Augmentation.

        Applies multiple augmentations and averages embeddings for more robust results.

        Args:
            image: PIL Image

        Returns:
            L2-normalized embedding vector as list of floats
        """
        if not self.use_tta or self.tta_augmentations <= 1:
            return self.embed_image(image)

        augmented_images = self._apply_tta_augmentations(image)

        with torch.no_grad():
            embeddings = []
            for aug_img in augmented_images:
                processed = self._preprocess_fn(aug_img).unsqueeze(0).to(self.device)
                features = self.model.encode_image(processed)
                features = features / features.norm(dim=-1, keepdim=True)
                embeddings.append(features)

            stacked = torch.cat(embeddings, dim=0)
            mean_embedding = stacked.mean(dim=0)
            mean_embedding = mean_embedding / mean_embedding.norm(dim=-1, keepdim=True)

        return mean_embedding.squeeze().cpu().tolist()

    def embed_image(self, image: Image.Image) -> list[float]:
        """Convenience method to preprocess and embed an image in one call.

        Args:
            image: PIL Image

        Returns:
            L2-normalized embedding vector as list of floats
        """
        pixel_values = self.preprocess(image)
        return self.embed(pixel_values)

    def embed_image_multiscale(
        self,
        image: Image.Image,
        scales: list[int] = None
    ) -> list[float]:
        """Generate embedding with multi-scale processing.

        Args:
            image: PIL Image
            scales: List of image sizes to process (default: [224, 336])

        Returns:
            L2-normalized embedding vector as list of floats
        """
        if scales is None:
            scales = [224, 336]

        with torch.no_grad():
            scale_embeddings = []
            for size in scales:
                resized = image.resize((size, size), Image.BILINEAR)
                processed = self._preprocess_fn(resized).unsqueeze(0).to(self.device)
                features = self.model.encode_image(processed)
                features = features / features.norm(dim=-1, keepdim=True)
                scale_embeddings.append(features)

            stacked = torch.cat(scale_embeddings, dim=0)
            mean_embedding = stacked.mean(dim=0)
            mean_embedding = mean_embedding / mean_embedding.norm(dim=-1, keepdim=True)

        return mean_embedding.squeeze().cpu().tolist()


def create_embedder(
    device: Optional[str] = None,
    use_tta: bool = True,
    tta_augmentations: int = 8
) -> Embedder:
    """Factory function to create an Embedder instance.

    Args:
        device: Device to use ('cuda', 'cpu', or None for auto-detect)
        use_tta: Enable Test-Time Augmentation for more robust embeddings
        tta_augmentations: Number of TTA augmentations (1-8)

    Returns:
        Configured Embedder instance
    """
    return Embedder(device=device, use_tta=use_tta, tta_augmentations=tta_augmentations)
