"""Inference API routes with rate limiting, logging, and metrics."""

import asyncio
import tempfile
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional
from functools import lru_cache

from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from PIL import Image

from ..models.response import (
    InferenceResponse,
    InsufficientConfidenceResponse,
    ErrorResponse,
    SimilarityStats,
)

router = APIRouter(prefix="/infer", tags=["inference"])

_pipeline = None
_executor = ThreadPoolExecutor(max_workers=2)
request_count = 0
request_times = []

logger = logging.getLogger(__name__)


def get_pipeline():
    """Get or create the inference pipeline."""
    global _pipeline
    if _pipeline is None:
        from satgeoinfer import create_pipeline
        logger.info("Initializing inference pipeline...")
        _pipeline = create_pipeline()
        logger.info("Pipeline initialized successfully")
    return _pipeline


async def _run_inference(pipeline, image: Image.Image, explain: bool, second_stage: bool):
    """Run inference in thread pool to avoid blocking event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor,
        lambda: pipeline.infer_from_image(
            image=image,
            explain=explain,
            second_stage=second_stage
        )
    )


@router.get("/stats")
async def get_inference_stats():
    """Get inference service statistics."""
    avg_time = sum(request_times) / len(request_times) if request_times else 0
    return {
        "total_requests": request_count,
        "average_latency_ms": round(avg_time * 1000, 2) if avg_time else 0,
        "recent_requests": len(request_times)
    }


@router.post(
    "",
    response_model=InferenceResponse,
    responses={
        200: {"model": InferenceResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def infer(
    request: Request,
    image: UploadFile = File(..., description="Satellite image to geolocate"),
    explain: bool = Query(False, description="Generate natural language explanation"),
    second_stage: bool = Query(False, description="Use second-stage clustering"),
) -> InferenceResponse:
    """Perform geolocation inference on a satellite image."""
    global request_count, request_times
    start_time = time.time()
    request_count += 1
    
    logger.info(f"Received inference request: {image.filename}")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            content = await image.read()
            if len(content) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail="Image too large. Maximum size is 10MB."
                )
            tmp.write(content)
            tmp_path = tmp.name

        try:
            image_obj = Image.open(tmp_path).convert("RGB")

            pipeline = get_pipeline()
            result = await _run_inference(
                pipeline, image_obj, explain, second_stage
            )

            if result.get("status") == "insufficient_confidence":
                return InsufficientConfidenceResponse(
                    message=result.get("message", "Insufficient candidates"),
                    candidates_retrieved=result.get("candidates_retrieved", 0)
                )

            sim_stats = result.get("similarity_stats")
            similarity_stats = None
            if sim_stats:
                similarity_stats = SimilarityStats(**sim_stats)

            return InferenceResponse(
                status="success",
                centroid_lat=result["centroid_lat"],
                centroid_lon=result["centroid_lon"],
                confidence_radius_km=result["confidence_radius_km"],
                confidence_level=result["confidence_level"],
                cluster_size=result["cluster_size"],
                total_candidates=result["total_candidates"],
                scene_distribution=result.get("scene_distribution", {}),
                secondary_clusters=result.get("secondary_clusters", []),
                similarity_stats=similarity_stats,
                explanation=result.get("explanation"),
                country=result.get("country"),
                country_code=result.get("country_code"),
                region=result.get("region"),
                city=result.get("city"),
                continent=result.get("continent")
            )

        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Inference failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Inference failed: {str(e)}"
        )
    finally:
        elapsed = time.time() - start_time
        request_times.append(elapsed)
        if len(request_times) > 100:
            request_times.pop(0)
        logger.info(f"Inference completed in {elapsed:.2f}s")


@router.post(
    "/batch",
    response_model=list[InferenceResponse],
    responses={
        200: {"model": InferenceResponse},
        500: {"model": ErrorResponse},
    },
)
async def infer_batch(
    images: list[UploadFile] = File(..., description="Batch of satellite images"),
    explain: bool = Query(False, description="Generate natural language explanation"),
    second_stage: bool = Query(False, description="Use second-stage clustering"),
) -> list[InferenceResponse]:
    """Perform batch geolocation inference on multiple satellite images."""
    global request_count, request_times
    start_time = time.time()
    request_count += 1
    
    if len(images) > 20:
        raise HTTPException(
            status_code=400,
            detail="Batch size too large. Maximum is 20 images."
        )
    
    logger.info(f"Received batch inference request: {len(images)} images")
    
    temp_files = []

    try:
        for uploaded_file in images:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                content = await uploaded_file.read()
                if len(content) > 10 * 1024 * 1024:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Image {uploaded_file.filename} too large."
                    )
                tmp.write(content)
                temp_files.append(tmp.name)

        pipeline = get_pipeline()
        pil_images = [Image.open(f).convert("RGB") for f in temp_files]

        tasks = [
            _run_inference(pipeline, img, explain, second_stage)
            for img in pil_images
        ]
        results = await asyncio.gather(*tasks)

        responses = []
        for result in results:
            if result.get("status") == "insufficient_confidence":
                responses.append(InsufficientConfidenceResponse(
                    message=result.get("message", "Insufficient candidates"),
                    candidates_retrieved=result.get("candidates_retrieved", 0)
                ))
            else:
                sim_stats = result.get("similarity_stats")
                similarity_stats = None
                if sim_stats:
                    similarity_stats = SimilarityStats(**sim_stats)

                responses.append(InferenceResponse(
                    status="success",
                    centroid_lat=result["centroid_lat"],
                    centroid_lon=result["centroid_lon"],
                    confidence_radius_km=result["confidence_radius_km"],
                    confidence_level=result["confidence_level"],
                    cluster_size=result["cluster_size"],
                    total_candidates=result["total_candidates"],
                    scene_distribution=result.get("scene_distribution", {}),
                    secondary_clusters=result.get("secondary_clusters", []),
                    similarity_stats=similarity_stats,
                    explanation=result.get("explanation"),
                    country=result.get("country"),
                    country_code=result.get("country_code"),
                    region=result.get("region"),
                    city=result.get("city"),
                    continent=result.get("continent")
                ))

        return responses

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch inference failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch inference failed: {str(e)}"
        )
    finally:
        for f in temp_files:
            Path(f).unlink(missing_ok=True)
        elapsed = time.time() - start_time
        request_times.append(elapsed)
        if len(request_times) > 100:
            request_times.pop(0)
        logger.info(f"Batch inference completed in {elapsed:.2f}s")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "satgeoinfer-inference"}
