import logging
from typing import List, Optional, Union
import numpy as np
import torch
import clip
from PIL import Image

logger = logging.getLogger(__name__)


class CLIPEmbeddingModel:
    """CLIP model for generating image embeddings."""
    
    def __init__(self, model_name: str = "ViT-B/32", device: str = "cuda"):
        """Initialize CLIP model.
        
        Args:
            model_name: CLIP model name (e.g., "ViT-B/32", "ViT-L/14")
            device: Device to run model on ("cuda" or "cpu")
        """
        self.model_name = model_name
        self.device = device
        
        logger.info(f"Loading CLIP model: {model_name}")
        try:
            self.model, self.preprocess = clip.load(model_name, device=device)
            self.model.eval()
            logger.info(f"CLIP model loaded on {device}")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise
    
    def get_embedding(
        self,
        image: Union[Image.Image, np.ndarray],
        normalize: bool = True
    ) -> np.ndarray:
        """Generate embedding for a single image.
        
        Args:
            image: Input image (PIL Image or numpy array)
            normalize: Whether to normalize embedding
            
        Returns:
            Embedding vector as numpy array
        """
        # Convert numpy to PIL if needed
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image.astype("uint8"))
        
        # Preprocess and get embedding
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            embedding = self.model.encode_image(image_input)
        
        # Convert to numpy
        embedding = embedding.cpu().numpy().astype(np.float32)
        
        # Normalize
        if normalize:
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        return embedding.flatten()
    
    def get_batch_embeddings(
        self,
        images: List[Union[Image.Image, np.ndarray]],
        batch_size: int = 32,
        normalize: bool = True
    ) -> List[np.ndarray]:
        """Generate embeddings for multiple images.
        
        Args:
            images: List of input images
            batch_size: Batch size for processing
            normalize: Whether to normalize embeddings
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            
            # Convert to PIL if needed
            batch_pil = []
            for img in batch:
                if isinstance(img, np.ndarray):
                    batch_pil.append(Image.fromarray(img.astype("uint8")))
                else:
                    batch_pil.append(img)
            
            # Preprocess batch
            image_inputs = torch.stack([
                self.preprocess(img) for img in batch_pil
            ]).to(self.device)
            
            # Get embeddings
            with torch.no_grad():
                batch_embeddings = self.model.encode_image(image_inputs)
            
            # Convert to numpy
            batch_embeddings = batch_embeddings.cpu().numpy().astype(np.float32)
            
            # Normalize
            if normalize:
                batch_embeddings = batch_embeddings / (
                    np.linalg.norm(batch_embeddings, axis=1, keepdims=True) + 1e-8
                )
            
            embeddings.extend([emb for emb in batch_embeddings])
        
        return embeddings
    
    def get_text_embedding(
        self,
        text: str,
        normalize: bool = True
    ) -> np.ndarray:
        """Generate embedding for text query.
        
        Args:
            text: Input text
            normalize: Whether to normalize embedding
            
        Returns:
            Embedding vector as numpy array
        """
        text_input = clip.tokenize(text).to(self.device)
        
        with torch.no_grad():
            embedding = self.model.encode_text(text_input)
        
        # Convert to numpy
        embedding = embedding.cpu().numpy().astype(np.float32)
        
        # Normalize
        if normalize:
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        return embedding.flatten()
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score (0-1)
        """
        # Normalize if not already
        emb1 = embedding1 / (np.linalg.norm(embedding1) + 1e-8)
        emb2 = embedding2 / (np.linalg.norm(embedding2) + 1e-8)
        
        similarity = np.dot(emb1, emb2)
        return float(similarity)
    
    def get_model_info(self) -> dict:
        """Get model information.
        
        Returns:
            Dictionary with model details
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "embedding_dim": self.model.visual.output_dim if hasattr(self.model, 'visual') else 512,
            "model_parameters": sum(p.numel() for p in self.model.parameters())
        }
