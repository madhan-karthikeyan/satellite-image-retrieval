import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np
from typing import List, Optional, Union
from pathlib import Path
import cv2
from app.core.config import settings


class EmbeddingService:
    def __init__(self):
        self.device = torch.device(settings.DEVICE if torch.cuda.is_available() else "cpu")
        self.model = self._load_model()
        self.transform = self._get_transform()
    
    def _load_model(self) -> nn.Module:
        model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
        model = nn.Sequential(*list(model.children())[:-1])
        model.eval()
        model.to(self.device)
        return model
    
    def _get_transform(self) -> transforms.Compose:
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    def extract_from_pil(self, image: Image.Image) -> np.ndarray:
        if image.mode != "RGB":
            image = image.convert("RGB")
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            features = self.model(tensor)
        return features.squeeze().cpu().numpy()
    
    def extract_from_array(self, array: np.ndarray) -> np.ndarray:
        if array.ndim == 3 and array.shape[2] in [3, 4]:
            array = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
        elif array.ndim == 2:
            array = cv2.cvtColor(array, cv2.COLOR_GRAY2RGB)
        
        image = Image.fromarray(array.astype(np.uint8))
        return self.extract_from_pil(image)
    
    def extract_from_tiff(self, tiff_path: Union[str, Path], bands: List[int] = None) -> np.ndarray:
        try:
            import rasterio
            with rasterio.open(tiff_path) as src:
                if bands:
                    data = src.read(bands)
                else:
                    data = src.read([1, 2, 3])
                
                data = np.transpose(data, (1, 2, 0))
                
                data = self._normalize_multispectral(data)
                
                rgb_image = self._create_rgb_composite(data)
                
                return self.extract_from_array(rgb_image)
        except ImportError:
            img = cv2.imread(str(tiff_path), cv2.IMREAD_UNCHANGED)
            if img is None:
                img = cv2.imread(str(tiff_path))
            if img is not None and len(img.shape) == 3:
                return self.extract_from_array(img)
            return np.random.rand(settings.EMBEDDING_DIM)
    
    def _normalize_multispectral(self, data: np.ndarray) -> np.ndarray:
        data = data.astype(np.float32)
        for i in range(data.shape[2]):
            band = data[:, :, i]
            p2, p98 = np.percentile(band, (2, 98))
            if p98 > p2:
                band = np.clip((band - p2) / (p98 - p2), 0, 1)
            data[:, :, i] = band
        return data
    
    def _create_rgb_composite(self, data: np.ndarray) -> np.ndarray:
        if data.shape[2] >= 3:
            rgb = data[:, :, :3]
            return (rgb * 255).astype(np.uint8)
        elif data.shape[2] == 4:
            rgb = data[:, :, [2, 1, 0]]
            return (rgb * 255).astype(np.uint8)
        return (data[:, :, 0:3] * 255).astype(np.uint8)
    
    def extract_chip(self, image_path: Union[str, Path], bbox: tuple) -> np.ndarray:
        x_min, y_min, x_max, y_max = bbox
        img = cv2.imread(str(image_path))
        if img is None:
            try:
                import rasterio
                with rasterio.open(image_path) as src:
                    data = src.read([1, 2, 3])
                    data = np.transpose(data, (1, 2, 0))
                    data = self._normalize_multispectral(data)
                    rgb = (data[:, :, :3] * 255).astype(np.uint8)
                    img = rgb
            except:
                return np.random.rand(settings.EMBEDDING_DIM)
        
        chip = img[y_min:y_max, x_min:x_max]
        return self.extract_from_array(chip)
    
    def compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        emb1 = emb1 / np.linalg.norm(emb1)
        emb2 = emb2 / np.linalg.norm(emb2)
        return float(np.dot(emb1, emb2))
    
    def get_embedding_dimension(self) -> int:
        return settings.EMBEDDING_DIM
    
    def get_device(self) -> str:
        return str(self.device)


embedding_service = EmbeddingService()
