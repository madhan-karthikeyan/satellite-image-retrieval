import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import after logging setup
from app.config import (
    API_HOST,
    API_PORT,
    DEBUG,
    DEVICE,
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_NAME,
    XVIEW_METADATA_FILE,
    DETECTION_SCORE_THRESHOLD,
    DETECTION_MAX_BOXES,
    ENABLE_DETECTION,
)
from app.services.chroma_service import ChromaService
from app.services.retrieval import RetrievalService
from app.services.detection import DetectionService
from app.services.dataset_loader import DatasetLoader, IndexBuilder
from app.routes import search, indexing


# Global instances
chroma_service: Optional[ChromaService] = None
retrieval_service: Optional[RetrievalService] = None
index_builder: Optional[IndexBuilder] = None
detection_service: Optional[DetectionService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    
    # Startup
    logger.info("=" * 80)
    logger.info("Satellite Intelligence System - Backend Starting")
    logger.info("=" * 80)
    
    try:
        logger.info(f"Device: {DEVICE}")
        logger.info(f"API: {API_HOST}:{API_PORT}")
        
        # Initialize ChromaDB service
        global chroma_service
        logger.info("Initializing ChromaDB...")
        chroma_service = ChromaService(
            persist_dir=CHROMA_PERSIST_DIR,
            collection_name=CHROMA_COLLECTION_NAME,
            device=DEVICE,
        )
        chroma_service.get_or_create_collection()
        logger.info("✓ ChromaDB initialized (%s)", CHROMA_PERSIST_DIR)
        
        # Initialize retrieval service
        global retrieval_service
        retrieval_service = RetrievalService(chroma_service)
        logger.info("✓ Retrieval service initialized")
        
        # Initialize dataset loader and index builder
        global index_builder
        dataset_loader = DatasetLoader()
        index_builder = IndexBuilder(chroma_service, dataset_loader)
        logger.info("✓ Index builder initialized")

        # Initialize detection service
        global detection_service
        if ENABLE_DETECTION:
            detection_service = DetectionService(
                score_threshold=DETECTION_SCORE_THRESHOLD,
                max_boxes=DETECTION_MAX_BOXES,
            )
            logger.info("✓ Detection service initialized")
        else:
            detection_service = None
            logger.info("Detection service disabled")
        
        # Inject services into route handlers
        setattr(search.router, "_retrieval_service", retrieval_service)
        setattr(search.router, "_detection_service", detection_service)
        setattr(indexing.router, "_index_builder", index_builder)
        
        # Build index from real metadata if available, else fallback to dummy index.
        collection_count = chroma_service.get_collection_count()
        if collection_count == 0:
            if XVIEW_METADATA_FILE.exists():
                logger.info("Found metadata file at %s. Building real xView index...", XVIEW_METADATA_FILE)
                metadata_list = dataset_loader.load_from_json(str(XVIEW_METADATA_FILE))
                if metadata_list:
                    stats = index_builder.build_index_from_metadata(
                        metadata_list=metadata_list,
                        image_dir=None,
                        batch_size=10,
                    )
                    logger.info("✓ Real index built: %s embeddings", stats["total_embeddings"])
                else:
                    logger.info("Metadata file is empty. Falling back to dummy index...")
                    stats = index_builder.build_dummy_index(num_chips=50, batch_size=10)
                    logger.info("✓ Dummy index built: %s embeddings", stats["total_embeddings"])
            else:
                logger.info("No metadata file found. Building initial dummy index...")
                stats = index_builder.build_dummy_index(num_chips=50, batch_size=10)
                logger.info("✓ Dummy index built: %s embeddings", stats["total_embeddings"])
        else:
            logger.info(f"✓ Index already contains {collection_count} embeddings")
        
        logger.info("=" * 80)
        logger.info("Backend Ready!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Backend shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Satellite Intelligence System",
    description="Visual search API for satellite imagery",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    collection_count = chroma_service.get_collection_count() if chroma_service else 0
    
    return {
        "status": "healthy",
        "service": "Satellite Intelligence System",
        "components": {
            "chroma_service": chroma_service is not None,
            "retrieval_service": retrieval_service is not None,
            "index_builder": index_builder is not None,
            "detection_service": detection_service is not None,
        },
        "index_status": {
            "total_embeddings": collection_count
        }
    }


# Include routers
app.include_router(search.router)
app.include_router(indexing.router)


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=DEBUG
    )
