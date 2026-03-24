import os
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
from PIL import Image

from app.services.embedding import embedding_service
from app.services.chroma import chroma_service
from app.core.config import settings
from app.schemas.models import SearchResult


class VisualSearchService:
    def __init__(self):
        self.embedding_service = embedding_service
        self.chroma_service = chroma_service
        self.sliding_window_sizes = [(128, 128), (256, 256), (384, 384)]
        self.stride = 64
    
    def process_uploaded_chip(
        self,
        image_path: str,
        object_name: str
    ) -> Tuple[str, Dict[str, Any]]:
        chip_id = f"{object_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        img = cv2.imread(image_path)
        if img is None:
            try:
                import rasterio
                with rasterio.open(image_path) as src:
                    data = src.read([1, 2, 3])
                    data = np.transpose(data, (1, 2, 0))
                    data = data.astype(np.float32)
                    for i in range(data.shape[2]):
                        band = data[:, :, i]
                        p2, p98 = np.percentile(band, (2, 98))
                        if p98 > p2:
                            band = np.clip((band - p2) / (p98 - p2), 0, 1)
                        data[:, :, i] = band
                    img = (data[:, :, :3] * 255).astype(np.uint8)
            except:
                raise ValueError(f"Could not read image: {image_path}")
        
        embedding = self.embedding_service.extract_from_array(img)
        
        metadata = {
            "object_name": object_name,
            "filename": os.path.basename(image_path),
            "width": img.shape[1],
            "height": img.shape[0],
            "channels": img.shape[2] if len(img.shape) == 3 else 1,
            "uploaded_at": datetime.now().isoformat()
        }
        
        self.chroma_service.add_chip(chip_id, embedding, metadata)
        
        return chip_id, metadata
    
    def process_drawn_box(
        self,
        image_path: str,
        bbox: Tuple[int, int, int, int],
        object_name: str
    ) -> Tuple[str, Dict[str, Any]]:
        chip_id = f"{object_name}_box_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        embedding = self.embedding_service.extract_chip(image_path, bbox)
        
        x_min, y_min, x_max, y_max = bbox
        metadata = {
            "object_name": object_name,
            "filename": os.path.basename(image_path),
            "bbox_x_min": x_min,
            "bbox_y_min": y_min,
            "bbox_x_max": x_max,
            "bbox_y_max": y_max,
            "uploaded_at": datetime.now().isoformat()
        }
        
        self.chroma_service.add_chip(chip_id, embedding, metadata)
        
        return chip_id, metadata
    
    def search_in_imagery(
        self,
        target_directory: str,
        object_name: Optional[str] = None,
        similarity_threshold: float = 0.65,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        results = []
        
        if not os.path.exists(target_directory):
            return results
        
        image_files = []
        for ext in ["*.tif", "*.tiff", "*.png", "*.jpg", "*.jpeg"]:
            image_files.extend(Path(target_directory).glob(ext))
            image_files.extend(Path(target_directory).glob(ext.upper()))
        
        chip_ids = self.chroma_service.list_object_names()
        
        if object_name:
            chip_ids = [object_name] if object_name in chip_ids else []
        
        if not chip_ids:
            return results
        
        for image_path in image_files:
            try:
                matches = self._search_in_single_image(
                    str(image_path),
                    chip_ids,
                    similarity_threshold,
                    max_results - len(results)
                )
                results.extend(matches)
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
            
            if len(results) >= max_results:
                break
        
        return results[:max_results]
    
    def _search_in_single_image(
        self,
        image_path: str,
        object_names: List[str],
        threshold: float,
        max_results: int
    ) -> List[Dict[str, Any]]:
        results = []
        
        try:
            img = cv2.imread(image_path)
            if img is None:
                try:
                    import rasterio
                    with rasterio.open(image_path) as src:
                        data = src.read([1, 2, 3])
                        data = np.transpose(data, (1, 2, 0))
                        data = data.astype(np.float32)
                        for i in range(data.shape[2]):
                            band = data[:, :, i]
                            p2, p98 = np.percentile(band, (2, 98))
                            if p98 > p2:
                                band = np.clip((band - p2) / (p98 - p2), 0, 1)
                            data[:, :, i] = band
                        img = (data[:, :, :3] * 255).astype(np.uint8)
                except:
                    return results
        except Exception as e:
            print(f"Error reading image {image_path}: {e}")
            return results
        
        h, w = img.shape[:2]
        
        for obj_name in object_names:
            sample_embedding = self._get_sample_embedding_for_object(obj_name)
            if sample_embedding is None:
                continue
            
            for window_size in self.sliding_window_sizes:
                win_h, win_w = window_size
                if win_h > h or win_w > w:
                    continue
                
                for y in range(0, h - win_h + 1, self.stride):
                    for x in range(0, w - win_w + 1, self.stride):
                        chip = img[y:y + win_h, x:x + win_w]
                        chip_embedding = self.embedding_service.extract_from_array(chip)
                        similarity = self.embedding_service.compute_similarity(
                            sample_embedding, chip_embedding
                        )
                        
                        if similarity >= threshold:
                            results.append({
                                "x_min": int(x),
                                "y_min": int(y),
                                "x_max": int(x + win_w),
                                "y_max": int(y + win_h),
                                "searched_object_name": obj_name,
                                "target_imagery_file_name": os.path.basename(image_path),
                                "similarity_score": round(similarity, 4)
                            })
                        
                        if len(results) >= max_results:
                            return results
        
        return results
    
    def _get_sample_embedding_for_object(self, object_name: str) -> Optional[np.ndarray]:
        search_results = self.chroma_service.search_similar(
            query_embedding=np.random.rand(settings.EMBEDDING_DIM),
            n_results=10,
            object_name=object_name
        )
        
        if search_results.get("embeddings"):
            return np.array(search_results["embeddings"][0])
        
        all_chips = self.chroma_service.collection.get(
            where={"object_name": object_name},
            include=["embeddings"]
        )
        
        if all_chips.get("embeddings") and len(all_chips["embeddings"]) > 0:
            return np.array(all_chips["embeddings"][0])
        
        return None
    
    def save_results_to_file(
        self,
        results: List[Dict[str, Any]],
        output_path: str,
        batch_name: str = "submission"
    ) -> str:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        if not output_path.endswith(".txt"):
            if not output_path.endswith("/"):
                output_path += "/"
            date_str = datetime.now().strftime("%d-%b-%Y")
            output_path += f"GC_PS03_{date_str}_{batch_name.replace(' ', '')}.txt"
        
        with open(output_path, "w") as f:
            for result in results:
                line = (
                    f"{result['x_min']} {result['y_min']} "
                    f"{result['x_max']} {result['y_max']} "
                    f"{result['searched_object_name']} "
                    f"{result['target_imagery_file_name']} "
                    f"{result['similarity_score']}"
                )
                f.write(line + "\n")
        
        return output_path


visual_search_service = VisualSearchService()
