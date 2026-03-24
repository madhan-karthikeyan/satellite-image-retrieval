import logging
from typing import List, Dict, Any, Optional
import json
import numpy as np

from app.services.chroma_service import ChromaService, EmbeddingCache

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for performing similarity search on satellite imagery."""
    
    def __init__(
        self,
        chroma_service: ChromaService
    ):
        """Initialize retrieval service.
        
        Args:
            chroma_service: ChromaDB service
        """
        self.chroma_service = chroma_service
        self.embedding_cache = EmbeddingCache(max_size=500)
        
        logger.info("Retrieval service initialized")
    
    def search_similar(
        self,
        query_image: np.ndarray,
        top_k: int = 10,
        similarity_threshold: float = 0.0,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar satellite images.
        
        Args:
            query_image: Query image as numpy array
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score
            filter_metadata: Optional metadata filter for ChromaDB
            
        Returns:
            List of result dictionaries with scores and metadata
        """
        # Search in ChromaDB using OpenCLIP embedding function.
        results = self.chroma_service.search_by_image(
            query_image=query_image,
            top_k=top_k,
            filter_dict=filter_metadata
        )
        
        # Process results
        processed_results = []
        
        if results["ids"] and len(results["ids"]) > 0:
            for i, (chip_id, distance, metadata) in enumerate(zip(
                results["ids"][0],
                results["distances"][0] if results["distances"] else [],
                results["metadatas"][0] if results["metadatas"] else []
            )):
                # Convert distance to similarity (cosine distance to similarity)
                # ChromaDB returns distances, we convert to similarity score
                similarity = 1 - distance if distance else 0.5
                
                if similarity < similarity_threshold:
                    continue
                
                result = {
                    "rank": len(processed_results),
                    "chip_id": chip_id,
                    "similarity_score": float(similarity),
                    "distance": float(distance) if distance else 0.0,
                }
                
                # Add metadata
                if metadata:
                    result.update(metadata)
                
                processed_results.append(result)
        
        logger.info(f"Found {len(processed_results)} similar results for query")
        return processed_results[:top_k]
    
    def batch_search(
        self,
        query_images: List[np.ndarray],
        top_k: int = 10,
        batch_size: int = 10
    ) -> List[List[Dict[str, Any]]]:
        """Search for similar images for multiple queries.
        
        Args:
            query_images: List of query images
            top_k: Number of top results per query
            batch_size: Batch size for processing
            
        Returns:
            List of result lists
        """
        all_results = []
        
        for i, query_image in enumerate(query_images):
            results = self.search_similar(query_image, top_k=top_k)
            all_results.append(results)
            logger.info(f"Processed query {i+1}/{len(query_images)}")
        
        return all_results
    
    def get_result_for_visualization(
        self,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format result for Cesium visualization.
        
        Args:
            result: Raw result dictionary
            
        Returns:
            Formatted result for visualization
        """
        return {
            "chip_id": result.get("chip_id"),
            "lat": result.get("lat_center", 0.0),
            "lon": result.get("lon_center", 0.0),
            "score": result.get("similarity_score", 0.0),
            "image_name": result.get("image_name", "unknown"),
            "bbox": result.get("bbox_pixel", [0, 0, 512, 512]),
            "confidence": result.get("similarity_score", 0.0)
        }
    
    def export_results_txt(
        self,
        results: List[Dict[str, Any]],
        output_path: str
    ) -> None:
        """Export results in evaluation format.
        
        Format: x_min y_min x_max y_max object_name image_name similarity_score
        
        Args:
            results: List of result dictionaries
            output_path: Path to save results
        """
        with open(output_path, 'w') as f:
            for result in results:
                bbox = result.get("bbox_pixel", [0, 0, 512, 512])
                x_min, y_min, x_max, y_max = bbox
                object_name = result.get("chip_id", "unknown")
                image_name = result.get("image_name", "unknown")
                score = result.get("similarity_score", 0.0)
                
                line = f"{x_min} {y_min} {x_max} {y_max} {object_name} {image_name} {score:.6f}\n"
                f.write(line)
        
        logger.info(f"Exported {len(results)} results to {output_path}")
    
    def export_results_json(
        self,
        results: List[Dict[str, Any]],
        output_path: str
    ) -> None:
        """Export results as JSON.
        
        Args:
            results: List of result dictionaries
            output_path: Path to save results
        """
        output_data = {
            "results": results,
            "count": len(results)
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Exported {len(results)} results to {output_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get retrieval service statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_embeddings": self.chroma_service.get_collection_count(),
            "cache_size": len(self.embedding_cache),
            "embedding_backend": self.chroma_service.get_embedding_backend_info(),
        }
