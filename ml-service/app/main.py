"""FastAPI application for SatGeoInfer."""

import os
import secrets
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Query, Header, Depends
from fastapi.middleware.cors import CORSMiddleware

project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

from satgeoinfer import Retriever
from .routes.infer import router as infer_router
from .models.response import (
    IndexStatsResponse,
    BuildIndexResponse,
)


ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
retriever_instance: Optional[Retriever] = None


def get_retriever() -> Retriever:
    """Get or create the retriever instance."""
    global retriever_instance
    if retriever_instance is None:
        chroma_env = os.getenv("CHROMA_PERSIST_DIR")
        if chroma_env:
            retriever_instance = Retriever(persist_dir=chroma_env)
        else:
            retriever_instance = Retriever()
    return retriever_instance


def verify_admin_key(x_admin_key: Optional[str] = Header(None)) -> str:
    """Verify admin API key for protected endpoints.

    Args:
        x_admin_key: Admin API key from header

    Returns:
        The verified API key

    Raises:
        HTTPException: If key is missing or invalid
    """
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Admin API not configured. Set ADMIN_API_KEY environment variable."
        )

    if not x_admin_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Admin-Key header"
        )

    if not secrets.compare_digest(x_admin_key, ADMIN_API_KEY):
        raise HTTPException(
            status_code=403,
            detail="Invalid admin API key"
        )

    return x_admin_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("Starting SatGeoInfer API...")
    yield
    print("Shutting down SatGeoInfer API...")


app = FastAPI(
    title="SatGeoInfer API",
    description="Satellite Image Geolocation Inference System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(infer_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "SatGeoInfer",
        "version": "1.0.0",
        "description": "Satellite Image Geolocation Inference System",
        "endpoints": {
            "/infer": "Perform geolocation inference on satellite images",
            "/index/stats": "Get index statistics",
            "/index/build": "Trigger index building (requires admin key)",
        }
    }


@app.get(
    "/index/stats",
    response_model=IndexStatsResponse,
    tags=["index"],
)
async def get_index_stats():
    """Get ChromaDB index statistics."""
    try:
        retriever = get_retriever()
        return IndexStatsResponse(
            collection_size=retriever.get_collection_size(),
            collection_name="fmow_embeddings"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get index stats: {str(e)}"
        )


@app.post(
    "/index/build",
    response_model=BuildIndexResponse,
    tags=["index"],
)
async def build_index(
    split: str = Query("train", description="Dataset split to index"),
    batch_size: int = Query(64, description="Batch size for processing"),
    _admin_key: str = Depends(verify_admin_key),
):
    """Trigger index building from fMoW dataset.

    Requires X-Admin-Key header with valid admin API key.
    """
    import subprocess
    import sys

    try:
        result = subprocess.run(
            [sys.executable, "scripts/build_index.py", "--split", split, "--batch-size", str(batch_size)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        retriever = get_retriever()
        total = retriever.get_collection_size()

        return BuildIndexResponse(
            status="completed",
            message=f"Index built for {split} split",
            total_indexed=total
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build index: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "satgeoinfer",
        "index_size": get_retriever().get_collection_size()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
