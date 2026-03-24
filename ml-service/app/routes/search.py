import logging
import io
import time
import tempfile
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.responses import FileResponse
import numpy as np
from PIL import Image

from app.services.retrieval import RetrievalService
from app.services.detection import DetectionService
from app.utils.image_processing import load_image_from_bytes, validate_image_file
from app.utils.geo_utils import pixel_to_latlon
from app.config import (
    MAX_FILE_SIZE,
    DEFAULT_TOP_K,
    MIN_SIMILARITY_THRESHOLD,
    UPLOADS_DIR,
)

router = APIRouter(prefix="/api", tags=["search"])

logger = logging.getLogger(__name__)


def get_retrieval_service() -> Optional[RetrievalService]:
    """Get retrieval service from app context."""
    # This will be injected by main.py
    return getattr(router, "_retrieval_service", None)


def get_detection_service() -> Optional[DetectionService]:
    """Get detection service from app context."""
    return getattr(router, "_detection_service", None)


def _safe_filename(name: Optional[str], fallback: str = "query.png") -> str:
    if not name:
        return fallback
    return Path(name).name or fallback


@router.post("/search")
async def search(
    image: UploadFile = File(...),
    top_k: int = Query(DEFAULT_TOP_K, ge=1, le=100),
    threshold: float = Query(MIN_SIMILARITY_THRESHOLD, ge=0.0, le=1.0),
    run_detection: bool = Query(True)
):
    """Search for similar satellite images.
    
    Args:
        image: Query image file
        top_k: Number of top results
        threshold: Minimum similarity threshold
        
    Returns:
        JSON with search results formatted for visualization
    """
    try:
        # Validate and load image
        file_content = await image.read()
        safe_name = _safe_filename(image.filename)
        validate_image_file(file_content, safe_name, MAX_FILE_SIZE)
        query_image = load_image_from_bytes(file_content)
        
        # Get retrieval service
        retrieval_service = get_retrieval_service()
        if not retrieval_service:
            raise HTTPException(
                status_code=503,
                detail="Retrieval service not initialized"
            )
        
        # Search
        start_time = time.time()
        results = retrieval_service.search_similar(
            query_image=query_image,
            top_k=top_k,
            similarity_threshold=threshold
        )
        search_time = time.time() - start_time
        
        # Optional detection and geo refinement on query image.
        detection_service = get_detection_service()
        best_detection = None
        if run_detection and detection_service is not None:
            best_detection = detection_service.best_detection(query_image)

        # Format for visualization
        visualization_results = [
            retrieval_service.get_result_for_visualization(result)
            for result in results
        ]

        # If detection exists, add derived lat/lon for each retrieval hit by
        # projecting detection center using each hit geobounds.
        if best_detection is not None:
            cx, cy = best_detection["center"]
            for idx, result in enumerate(results):
                lat = float(visualization_results[idx].get("lat", 0.0))
                lon = float(visualization_results[idx].get("lon", 0.0))
                width = int(result.get("image_width", 512))
                height = int(result.get("image_height", 512))
                lat_top = float(result.get("lat_top", lat + 0.01))
                lon_left = float(result.get("lon_left", lon - 0.01))
                lat_bottom = float(result.get("lat_bottom", lat - 0.01))
                lon_right = float(result.get("lon_right", lon + 0.01))

                det_lat, det_lon = pixel_to_latlon(
                    x=float(cx),
                    y=float(cy),
                    width=width,
                    height=height,
                    lat_top=lat_top,
                    lon_left=lon_left,
                    lat_bottom=lat_bottom,
                    lon_right=lon_right,
                )

                visualization_results[idx]["detection"] = {
                    "bbox": best_detection["bbox"],
                    "score": best_detection["score"],
                    "label": best_detection["label"],
                    "lat": float(det_lat),
                    "lon": float(det_lon),
                }
        
        logger.info(f"Search completed in {search_time:.2f}s, found {len(visualization_results)} results")
        
        return {
            "success": True,
            "results": visualization_results,
            "count": len(visualization_results),
            "search_time_ms": search_time * 1000,
            "detection_enabled": run_detection,
            "query_detection": best_detection,
        }
    
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/search/export-txt")
async def search_and_export_txt(
    image: UploadFile = File(...),
    top_k: int = Query(DEFAULT_TOP_K, ge=1, le=100),
    threshold: float = Query(MIN_SIMILARITY_THRESHOLD, ge=0.0, le=1.0)
):
    """Search and export results in evaluation format.
    
    Format: x_min y_min x_max y_max object_name image_name similarity_score
    """
    try:
        # Validate and load image
        file_content = await image.read()
        safe_name = _safe_filename(image.filename)
        validate_image_file(file_content, safe_name, MAX_FILE_SIZE)
        query_image = load_image_from_bytes(file_content)
        
        # Get retrieval service
        retrieval_service = get_retrieval_service()
        if not retrieval_service:
            raise HTTPException(
                status_code=503,
                detail="Retrieval service not initialized"
            )
        
        # Search
        results = retrieval_service.search_similar(
            query_image=query_image,
            top_k=top_k,
            similarity_threshold=threshold
        )
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", dir=str(UPLOADS_DIR)) as temp_file:
            output_path = temp_file.name
        retrieval_service.export_results_txt(results, output_path)
        
        return FileResponse(
            path=output_path,
            media_type="text/plain",
            filename="search_results.txt"
        )
    
    except Exception as e:
        logger.error(f"Export error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/search/export-json")
async def search_and_export_json(
    image: UploadFile = File(...),
    top_k: int = Query(DEFAULT_TOP_K, ge=1, le=100),
    threshold: float = Query(MIN_SIMILARITY_THRESHOLD, ge=0.0, le=1.0)
):
    """Search and export results as JSON."""
    try:
        # Validate and load image
        file_content = await image.read()
        safe_name = _safe_filename(image.filename)
        validate_image_file(file_content, safe_name, MAX_FILE_SIZE)
        query_image = load_image_from_bytes(file_content)
        
        # Get retrieval service
        retrieval_service = get_retrieval_service()
        if not retrieval_service:
            raise HTTPException(
                status_code=503,
                detail="Retrieval service not initialized"
            )
        
        # Search
        results = retrieval_service.search_similar(
            query_image=query_image,
            top_k=top_k,
            similarity_threshold=threshold
        )
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", dir=str(UPLOADS_DIR)) as temp_file:
            output_path = temp_file.name
        retrieval_service.export_results_json(results, output_path)
        
        return FileResponse(
            path=output_path,
            media_type="application/json",
            filename="search_results.json"
        )
    
    except Exception as e:
        logger.error(f"Export error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/stats")
async def search_stats():
    """Get search service statistics."""
    try:
        retrieval_service = get_retrieval_service()
        if not retrieval_service:
            raise HTTPException(
                status_code=503,
                detail="Retrieval service not initialized"
            )
        
        stats = retrieval_service.get_statistics()
        return {
            "success": True,
            "stats": stats
        }
    
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/detect")
async def detect_objects(
    image: UploadFile = File(...),
):
    """Run object detection on a query image.

    Returns detection boxes/scores for satellite imagery refinement.
    """
    try:
        file_content = await image.read()
        safe_name = _safe_filename(image.filename)
        validate_image_file(file_content, safe_name, MAX_FILE_SIZE)
        query_image = load_image_from_bytes(file_content)

        detection_service = get_detection_service()
        if detection_service is None:
            raise HTTPException(status_code=503, detail="Detection service not initialized")

        detections = detection_service.detect(query_image)
        return {
            "success": True,
            "count": len(detections),
            "detections": detections,
        }
    except ValueError as e:
        logger.warning("Detection validation error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Detection error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
