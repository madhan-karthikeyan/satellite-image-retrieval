"""Vector database retrieval with ensemble strategies for improved accuracy."""

import os
from pathlib import Path
from typing import Optional, Literal
from collections import defaultdict
import chromadb
from chromadb.config import Settings


def get_project_root() -> Path:
    """Get the project root directory (parent of ml-service)."""
    return Path(__file__).parent.parent


class Retriever:
    """ChromaDB-based image retrieval with ensemble support."""

    COLLECTION_NAME = "fmow_embeddings"
    PERSIST_DIR = "./chroma_index"

    DEFAULT_RETRY_SCHEDULE = [
        {"top_k": 100, "threshold": 0.65},
        {"top_k": 200, "threshold": 0.55},
        {"top_k": 500, "threshold": 0.45},
    ]
    
    MIN_CANDIDATES = 10
    MAX_RETRIES = 3

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        retry_schedule: Optional[list[dict]] = None,
        ensemble_strategy: Literal["rrf", "weighted", "hybrid"] = "rrf"
    ):
        """Initialize retriever with ChromaDB client.

        Args:
            persist_dir: Directory for persistent storage
            retry_schedule: List of retry configurations with top_k and threshold
            ensemble_strategy: Fusion strategy for multiple retrieval passes
                - 'rrf': Reciprocal Rank Fusion
                - 'weighted': Weighted score fusion
                - 'hybrid': Combination of both
        """
        if persist_dir is None:
            project_root = get_project_root()
            persist_dir = str(project_root / "chroma_index")
        
        self.persist_dir = persist_dir
        self.retry_schedule = retry_schedule or self.DEFAULT_RETRY_SCHEDULE
        self.ensemble_strategy = ensemble_strategy
        
        os.makedirs(self.persist_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "fMoW satellite image embeddings"}
        )

    def _l2_to_cosine(self, l2_distance: float) -> float:
        """Convert squared L2 distance to cosine similarity for normalized vectors."""
        return 1.0 - (l2_distance / 2.0)

    def store(
        self,
        image_id: str,
        embedding: list[float],
        lat: float,
        lon: float,
        scene_label: str
    ) -> None:
        """Store an image embedding with metadata."""
        self.collection.upsert(
            ids=[image_id],
            embeddings=[embedding],
            metadatas=[{
                "lat": lat,
                "lon": lon,
                "scene_label": scene_label
            }],
            documents=[scene_label]
        )

    def _reciprocal_rank_fusion(
        self,
        result_lists: list[list[dict]],
        k: int = 60
    ) -> list[dict]:
        """Apply Reciprocal Rank Fusion to combine multiple result sets.
        
        RRF formula: 1 / (k + rank)
        
        Args:
            result_lists: List of ranked result lists
            k: RRF constant (higher = less weight to rank)
            
        Returns:
            Fused and reranked results
        """
        scores = defaultdict(float)
        doc_scores = {}

        for result_list in result_lists:
            for rank, doc in enumerate(result_list, 1):
                doc_id = doc["image_id"]
                rrf_score = 1.0 / (k + rank)
                scores[doc_id] += rrf_score
                doc_scores[doc_id] = doc

        reranked = sorted(
            [(doc_id, score) for doc_id, score in scores.items()],
            key=lambda x: x[1],
            reverse=True
        )

        fused_results = []
        for doc_id, score in reranked:
            doc = doc_scores[doc_id].copy()
            doc["rrf_score"] = float(score)
            fused_results.append(doc)

        return fused_results

    def _weighted_score_fusion(
        self,
        result_lists: list[list[dict]],
        weights: list[float] = None
    ) -> list[dict]:
        """Apply weighted score fusion to combine results.
        
        Args:
            result_lists: List of result lists with similarity scores
            weights: Weights for each result list (default: equal weights)
            
        Returns:
            Fused and reranked results
        """
        if weights is None:
            weights = [1.0 / len(result_lists)] * len(result_lists)
        
        weights = [w / sum(weights) for w in weights]
        
        scores = defaultdict(float)
        doc_scores = {}

        for result_list, weight in zip(result_lists, weights):
            for doc in result_list:
                doc_id = doc["image_id"]
                scores[doc_id] += weight * doc["similarity"]
                doc_scores[doc_id] = doc

        reranked = sorted(
            [(doc_id, score) for doc_id, score in scores.items()],
            key=lambda x: x[1],
            reverse=True
        )

        fused_results = []
        for doc_id, score in reranked:
            doc = doc_scores[doc_id].copy()
            doc["fused_score"] = float(score)
            fused_results.append(doc)

        return fused_results

    def _apply_ensemble_fusion(
        self,
        result_lists: list[list[dict]]
    ) -> list[dict]:
        """Apply ensemble fusion strategy to combine results."""
        if len(result_lists) == 1:
            return result_lists[0]
        
        if self.ensemble_strategy == "rrf":
            return self._reciprocal_rank_fusion(result_lists)
        elif self.ensemble_strategy == "weighted":
            return self._weighted_score_fusion(result_lists)
        else:
            rrf_results = self._reciprocal_rank_fusion(result_lists)
            weighted_results = self._weighted_score_fusion(result_lists)
            
            combined = {}
            for i, doc in enumerate(rrf_results):
                doc_id = doc["image_id"]
                combined[doc_id] = {
                    **doc,
                    "hybrid_score": 0.5 * (1.0 / (60 + i + 1)) + 0.5 * doc.get("fused_score", 0)
                }
            
            for doc in weighted_results:
                doc_id = doc["image_id"]
                if doc_id in combined:
                    combined[doc_id]["hybrid_score"] = (
                        0.5 * combined[doc_id].get("rrf_score", 0) / (combined[doc_id].get("rrf_score", 1) or 1) +
                        0.5 * doc.get("fused_score", 0)
                    )
            
            return sorted(
                combined.values(),
                key=lambda x: x.get("hybrid_score", 0),
                reverse=True
            )

    def retrieve(
        self,
        query_embedding: list[float],
        top_k: int = 100,
        sim_threshold: float = 0.65,
        use_ensemble: bool = True
    ) -> list[dict]:
        """Retrieve similar images with optional ensemble fusion.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to retrieve
            sim_threshold: Minimum similarity threshold
            use_ensemble: Use ensemble fusion with multiple retrieval passes
            
        Returns:
            List of candidate dictionaries with image_id, similarity, lat, lon, scene_label
        """
        if not use_ensemble or len(self.retry_schedule) <= 1:
            return self._retrieve_single_pass(query_embedding, top_k, sim_threshold)
        
        result_lists = []
        for config in self.retry_schedule[:2]:
            result_list = self._retrieve_single_pass(
                query_embedding,
                config["top_k"],
                config["threshold"]
            )
            result_lists.append(result_list)
        
        fused_results = self._apply_ensemble_fusion(result_lists)
        
        filtered = [
            {**r, "similarity": r.get("similarity", r.get("fused_score", 0))}
            for r in fused_results
            if r.get("similarity", 0) >= sim_threshold
        ]
        
        seen_ids = set()
        unique_results = []
        for r in filtered:
            if r["image_id"] not in seen_ids:
                seen_ids.add(r["image_id"])
                unique_results.append(r)
        
        return unique_results[:top_k] if len(unique_results) >= self.MIN_CANDIDATES else fused_results[:self.MIN_CANDIDATES]

    def _retrieve_single_pass(
        self,
        query_embedding: list[float],
        top_k: int,
        sim_threshold: float
    ) -> list[dict]:
        """Single-pass retrieval without ensemble."""
        seen_ids: set[str] = set()
        candidates: list[dict] = []

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
        except Exception:
            return candidates

        if not results or not results.get("ids") or not results["ids"]:
            return candidates

        batch_ids = results["ids"][0]
        batch_distances = results["distances"][0] if results.get("distances") else []
        batch_metadatas = results["metadatas"][0] if results.get("metadatas") else []

        for i, img_id in enumerate(batch_ids):
            if img_id in seen_ids:
                continue

            distance = batch_distances[i] if i < len(batch_distances) else 0.0
            meta = batch_metadatas[i] if i < len(batch_metadatas) else {}

            similarity = self._l2_to_cosine(distance)

            if similarity >= sim_threshold:
                seen_ids.add(img_id)
                candidates.append({
                    "image_id": img_id,
                    "similarity": float(similarity),
                    "lat": meta.get("lat", 0.0),
                    "lon": meta.get("lon", 0.0),
                    "scene_label": meta.get("scene_label", "unknown")
                })

        return candidates

    def retrieve_by_region(
        self,
        query_embedding: list[float],
        region_bounds: dict,
        top_k: int = 50
    ) -> list[dict]:
        """Retrieve images within a geographic region.
        
        Args:
            query_embedding: Query embedding vector
            region_bounds: Dict with min_lat, max_lat, min_lon, max_lon
            top_k: Maximum results to return
            
        Returns:
            Filtered candidate list within region
        """
        where_filter = {
            "$and": [
                {"lat": {"$gte": region_bounds.get("min_lat", -90)}},
                {"lat": {"$lte": region_bounds.get("max_lat", 90)}},
                {"lon": {"$gte": region_bounds.get("min_lon", -180)}},
                {"lon": {"$lte": region_bounds.get("max_lon", 180)}}
            ]
        }
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 2,
                where=where_filter
            )
        except Exception:
            return []

        if not results or not results.get("ids") or not results["ids"]:
            return []

        candidates = []
        batch_ids = results["ids"][0]
        batch_distances = results["distances"][0] if results.get("distances") else []
        batch_metadatas = results["metadatas"][0] if results.get("metadatas") else []

        for i, img_id in enumerate(batch_ids[:top_k]):
            distance = batch_distances[i] if i < len(batch_distances) else 0.0
            meta = batch_metadatas[i] if i < len(batch_metadatas) else {}

            candidates.append({
                "image_id": img_id,
                "similarity": float(self._l2_to_cosine(distance)),
                "lat": meta.get("lat", 0.0),
                "lon": meta.get("lon", 0.0),
                "scene_label": meta.get("scene_label", "unknown")
            })

        return candidates

    def get_collection_size(self) -> int:
        """Get the number of items in the collection."""
        return self.collection.count()

    def get_all_ids(self) -> set[str]:
        """Get all IDs currently in the collection."""
        try:
            result = self.collection.get()
            return set(result["ids"]) if result and result.get("ids") else set()
        except Exception:
            return set()


def create_retriever(
    persist_dir: Optional[str] = None,
    retry_schedule: Optional[list[dict]] = None,
    ensemble_strategy: Literal["rrf", "weighted", "hybrid"] = "rrf"
) -> Retriever:
    """Factory function to create a Retriever instance."""
    return Retriever(
        persist_dir=persist_dir,
        retry_schedule=retry_schedule,
        ensemble_strategy=ensemble_strategy
    )
