import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Optional, Dict, Any
import numpy as np
from pathlib import Path
from app.core.config import settings


class ChromaService:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(settings.CHROMA_DIR),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collection_name = "satellite_chips"
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        try:
            return self.client.get_collection(name=self.collection_name)
        except:
            return self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Satellite image chip embeddings for visual search"}
            )
    
    def add_chip(
        self,
        chip_id: str,
        embedding: np.ndarray,
        metadata: Dict[str, Any]
    ) -> bool:
        try:
            self.collection.add(
                ids=[chip_id],
                embeddings=[embedding.tolist()],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            print(f"Error adding chip: {e}")
            return False
    
    def add_chips_batch(
        self,
        chip_ids: List[str],
        embeddings: List[np.ndarray],
        metadatas: List[Dict[str, Any]]
    ) -> bool:
        try:
            self.collection.add(
                ids=chip_ids,
                embeddings=[e.tolist() for e in embeddings],
                metadatas=metadatas
            )
            return True
        except Exception as e:
            print(f"Error adding chips batch: {e}")
            return False
    
    def search_similar(
        self,
        query_embedding: np.ndarray,
        n_results: int = 10,
        where: Optional[Dict] = None,
        object_name: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            where_filter = {}
            if object_name:
                where_filter["object_name"] = object_name
            if where:
                where_filter.update(where)
            
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                where=where_filter if where_filter else None,
                include=["metadatas", "distances", "embeddings"]
            )
            
            return {
                "ids": results["ids"][0] if results["ids"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "embeddings": results["embeddings"][0] if results.get("embeddings") else []
            }
        except Exception as e:
            print(f"Error searching: {e}")
            return {"ids": [], "distances": [], "metadatas": [], "embeddings": []}
    
    def get_chip(self, chip_id: str) -> Optional[Dict[str, Any]]:
        try:
            result = self.collection.get(
                ids=[chip_id],
                include=["metadatas", "embeddings"]
            )
            if result["ids"]:
                return {
                    "id": result["ids"][0],
                    "embedding": result["embeddings"][0] if result.get("embeddings") else None,
                    "metadata": result["metadatas"][0] if result.get("metadatas") else None
                }
            return None
        except Exception as e:
            print(f"Error getting chip: {e}")
            return None
    
    def delete_chip(self, chip_id: str) -> bool:
        try:
            self.collection.delete(ids=[chip_id])
            return True
        except Exception as e:
            print(f"Error deleting chip: {e}")
            return False
    
    def delete_by_object_name(self, object_name: str) -> bool:
        try:
            self.collection.delete(where={"object_name": object_name})
            return True
        except Exception as e:
            print(f"Error deleting by object name: {e}")
            return False
    
    def count_chips(self, object_name: Optional[str] = None) -> int:
        try:
            if object_name:
                return len(self.collection.get(where={"object_name": object_name})["ids"])
            return self.collection.count()
        except:
            return 0
    
    def list_object_names(self) -> List[str]:
        try:
            all_data = self.collection.get(include=["metadatas"])
            object_names = set()
            for metadata in all_data.get("metadatas", []):
                if metadata and "object_name" in metadata:
                    object_names.add(metadata["object_name"])
            return list(object_names)
        except:
            return []
    
    def reset(self) -> bool:
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self._get_or_create_collection()
            return True
        except Exception as e:
            print(f"Error resetting: {e}")
            return False


chroma_service = ChromaService()
