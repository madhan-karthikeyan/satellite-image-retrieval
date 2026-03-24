import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from tqdm import tqdm

from app.services.chroma_service import ChromaService
from app.utils.geo_utils import get_dummy_geobounds
from app.utils.image_processing import create_random_chip, load_image_from_path


logger = logging.getLogger(__name__)


class DatasetLoader:
    """Loads and manages xView metadata."""

    def __init__(self, dataset_path: Optional[str] = None):
        self.dataset_path = dataset_path
        self.chips_metadata: List[Dict[str, Any]] = []

    def load_from_json(self, json_path: str) -> List[Dict[str, Any]]:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                self.chips_metadata = json.load(f)
            logger.info("Loaded %d chip metadata from %s", len(self.chips_metadata), json_path)
            return self.chips_metadata
        except FileNotFoundError:
            logger.warning("Metadata file not found: %s", json_path)
            return []

    def save_metadata(self, output_path: str) -> None:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.chips_metadata, f, indent=2)
        logger.info("Saved metadata for %d chips to %s", len(self.chips_metadata), output_path)

    def generate_dummy_chips(self, num_chips: int = 100, chip_size: int = 512) -> List[Dict[str, Any]]:
        chips: List[Dict[str, Any]] = []
        for i in range(num_chips):
            chip_id = f"chip_{i:06d}"
            x_min = int(np.random.randint(0, chip_size - 100))
            y_min = int(np.random.randint(0, chip_size - 100))
            x_max = int(min(x_min + np.random.randint(50, 200), chip_size))
            y_max = int(min(y_min + np.random.randint(50, 200), chip_size))

            geo_bounds = get_dummy_geobounds(chip_id, seed=i)
            chips.append(
                {
                    "chip_id": chip_id,
                    "image_name": f"xview_scene_{i // 10:03d}.tif",
                    "bbox_pixel": [x_min, y_min, x_max, y_max],
                    "image_width": chip_size,
                    "image_height": chip_size,
                    "lat_top": geo_bounds["lat_top"],
                    "lon_left": geo_bounds["lon_left"],
                    "lat_bottom": geo_bounds["lat_bottom"],
                    "lon_right": geo_bounds["lon_right"],
                    "lat_center": (geo_bounds["lat_top"] + geo_bounds["lat_bottom"]) / 2,
                    "lon_center": (geo_bounds["lon_left"] + geo_bounds["lon_right"]) / 2,
                }
            )

        self.chips_metadata = chips
        logger.info("Generated %d dummy chips", num_chips)
        return chips


class IndexBuilder:
    """Builds and manages OpenCLIP-backed Chroma image index."""

    def __init__(self, chroma_service: ChromaService, dataset_loader: DatasetLoader):
        self.chroma_service = chroma_service
        self.dataset_loader = dataset_loader

    def build_index_from_images(self, image_paths: List[str], batch_size: int = 32) -> Dict[str, Any]:
        logger.info("Building index from %d images", len(image_paths))

        ids: List[str] = []
        images: List[np.ndarray] = []
        metadatas: List[Dict[str, Any]] = []

        for i, image_path in enumerate(tqdm(image_paths, desc="Indexing images")):
            try:
                image = load_image_from_path(image_path)
                chip_id = f"chip_{i:06d}"
                ids.append(chip_id)
                images.append(image)
                metadatas.append(
                    {
                        "image_name": Path(image_path).name,
                        "bbox_pixel": [0, 0, int(image.shape[1]), int(image.shape[0])],
                        "image_width": int(image.shape[1]),
                        "image_height": int(image.shape[0]),
                        "lat_top": 85.0,
                        "lon_left": -180.0,
                        "lat_bottom": -85.0,
                        "lon_right": 180.0,
                        "lat_center": 0.0,
                        "lon_center": 0.0,
                    }
                )
            except Exception as e:
                logger.error("Failed to process image %s: %s", image_path, e)

        if ids:
            self.chroma_service.batch_add_images(ids=ids, images=images, metadata_list=metadatas, batch_size=batch_size)

        stats = {
            "total_embeddings": len(ids),
            "collection_count": self.chroma_service.get_collection_count(),
            "embedding_backend": self.chroma_service.get_embedding_backend_info(),
        }
        logger.info("Index built with %d entries", stats["total_embeddings"])
        return stats

    def build_index_from_metadata(
        self,
        metadata_list: List[Dict[str, Any]],
        image_dir: Optional[str] = None,
        batch_size: int = 32,
    ) -> Dict[str, Any]:
        logger.info("Building index from %d metadata entries", len(metadata_list))

        ids: List[str] = []
        images: List[np.ndarray] = []
        metadatas: List[Dict[str, Any]] = []

        for i, meta in enumerate(tqdm(metadata_list, desc="Processing metadata")):
            try:
                chip_id = str(meta.get("chip_id", f"chip_{i:06d}"))

                chip_path = meta.get("chip_path")
                if chip_path and Path(str(chip_path)).exists():
                    image = load_image_from_path(str(chip_path))
                elif image_dir and meta.get("image_name"):
                    image_path = Path(image_dir) / str(meta["image_name"])
                    if image_path.exists():
                        image = load_image_from_path(str(image_path))
                    else:
                        image = create_random_chip()
                else:
                    image = create_random_chip()

                filtered_meta = {
                    k: v
                    for k, v in meta.items()
                    if k
                    in {
                        "image_name",
                        "bbox_pixel",
                        "image_width",
                        "image_height",
                        "lat_top",
                        "lon_left",
                        "lat_bottom",
                        "lon_right",
                        "lat_center",
                        "lon_center",
                        "type_id",
                        "feature_id",
                        "chip_path",
                    }
                }

                ids.append(chip_id)
                images.append(image)
                metadatas.append(filtered_meta)
            except Exception as e:
                logger.error("Failed metadata entry %d: %s", i, e)

        if ids:
            self.chroma_service.batch_add_images(ids=ids, images=images, metadata_list=metadatas, batch_size=batch_size)

        stats = {
            "total_embeddings": len(ids),
            "collection_count": self.chroma_service.get_collection_count(),
            "embedding_backend": self.chroma_service.get_embedding_backend_info(),
        }
        logger.info("Index built with %d entries", stats["total_embeddings"])
        return stats

    def build_dummy_index(self, num_chips: int = 100, batch_size: int = 32) -> Dict[str, Any]:
        logger.info("Building dummy index with %d chips", num_chips)
        dummy_metadata = self.dataset_loader.generate_dummy_chips(num_chips)
        return self.build_index_from_metadata(dummy_metadata, batch_size=batch_size)
