import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
import numpy as np
from chromadb.api.models.Collection import Collection
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction


logger = logging.getLogger(__name__)


def _coerce_metadata_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    sanitized: Dict[str, Any] = {}
    for key, value in metadata.items():
        if isinstance(value, list):
            sanitized[key] = ",".join(str(v) for v in value)
        else:
            sanitized[key] = _coerce_metadata_value(value)
    return sanitized


class ChromaService:
    """Service for managing satellite chip vectors in modern ChromaDB.

    Uses PersistentClient + OpenCLIPEmbeddingFunction.
    """

    def __init__(
        self,
        persist_dir: str,
        collection_name: str = "satellite_chips",
        model_name: str = "ViT-B-32",
        checkpoint: str = "laion2b_s34b_b79k",
        device: str = "cpu",
    ):
        self.persist_dir = str(persist_dir)
        self.collection_name = collection_name
        self.model_name = model_name
        self.checkpoint = checkpoint
        self.device = device

        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        self.embedding_function = OpenCLIPEmbeddingFunction(
            model_name=self.model_name,
            checkpoint=self.checkpoint,
            device=self.device,
        )

        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection: Optional[Collection] = None

    def get_or_create_collection(self) -> Collection:
        if self.collection is None:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"},
            )
        return self.collection

    def add_images(
        self,
        ids: List[str],
        images: List[np.ndarray],
        metadata_list: List[Dict[str, Any]],
    ) -> None:
        if not (len(ids) == len(images) == len(metadata_list)):
            raise ValueError("ids, images and metadata_list must have same length")

        collection = self.get_or_create_collection()
        sanitized_metadatas: Any = [sanitize_metadata(m) for m in metadata_list]

        collection.add(
            ids=ids,
            images=images,
            metadatas=sanitized_metadatas,
        )
        logger.info("Added %d image records to collection", len(ids))

    def batch_add_images(
        self,
        ids: List[str],
        images: List[np.ndarray],
        metadata_list: List[Dict[str, Any]],
        batch_size: int = 64,
    ) -> None:
        total = len(ids)
        for i in range(0, total, batch_size):
            end_idx = min(i + batch_size, total)
            self.add_images(
                ids=ids[i:end_idx],
                images=images[i:end_idx],
                metadata_list=metadata_list[i:end_idx],
            )

    def search_by_image(
        self,
        query_image: np.ndarray,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> Any:
        collection = self.get_or_create_collection()
        return collection.query(
            query_images=[query_image],
            n_results=top_k,
            where=filter_dict if filter_dict else None,
            include=["metadatas", "distances"],
        )

    def search_by_text(
        self,
        query_text: str,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> Any:
        collection = self.get_or_create_collection()
        return collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=filter_dict if filter_dict else None,
            include=["metadatas", "distances"],
        )

    def get_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        collection = self.get_or_create_collection()
        results = collection.get(ids=[item_id], include=["metadatas"])
        ids = results.get("ids") or []
        metadatas = results.get("metadatas") or []
        if not ids:
            return None
        metadata = metadatas[0] if metadatas else None
        return {"id": ids[0], "metadata": metadata}

    def get_collection_count(self) -> int:
        collection = self.get_or_create_collection()
        return collection.count()

    def get_embedding_backend_info(self) -> Dict[str, Any]:
        return {
            "provider": "chromadb-openclip",
            "model_name": self.model_name,
            "checkpoint": self.checkpoint,
            "device": self.device,
        }

    def delete_collection(self) -> None:
        self.client.delete_collection(name=self.collection_name)
        self.collection = None
        logger.info("Deleted collection: %s", self.collection_name)

    def reset(self) -> None:
        # Keep for compatibility. Chroma PersistentClient does not expose reset in the same way.
        self.delete_collection()

    def persist(self) -> None:
        # PersistentClient auto-persists.
        logger.info("PersistentClient auto-persists; no explicit persist call required")


class EmbeddingCache:
    """In-memory cache for embeddings or query artifacts."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, np.ndarray] = {}

    def get(self, key: str) -> Optional[np.ndarray]:
        return self.cache.get(key)

    def set(self, key: str, embedding: np.ndarray) -> None:
        if len(self.cache) >= self.max_size:
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = embedding

    def clear(self) -> None:
        self.cache.clear()

    def __len__(self) -> int:
        return len(self.cache)
