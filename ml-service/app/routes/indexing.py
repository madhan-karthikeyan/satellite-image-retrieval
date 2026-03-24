import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.services.dataset_loader import IndexBuilder
from app.config import (
    XVIEW_METADATA_FILE,
    XVIEW_TRAIN_IMAGES_DIR,
    XVIEW_TRAIN_LABELS_FILE,
    XVIEW_CHIP_SIZE,
    XVIEW_CHIP_OVERLAP,
)

router = APIRouter(prefix="/api", tags=["indexing"])

logger = logging.getLogger(__name__)


def get_index_builder() -> Optional[IndexBuilder]:
    """Get index builder from app context."""
    return getattr(router, "_index_builder", None)


@router.post("/index/build")
async def build_index(background_tasks: BackgroundTasks):
    """Build embedding index from dummy data.
    
    This is a demo endpoint. In production, this would load from actual dataset.
    """
    try:
        index_builder = get_index_builder()
        if not index_builder:
            raise HTTPException(
                status_code=503,
                detail="Index builder not initialized"
            )
        
        metadata_file = Path(XVIEW_METADATA_FILE)

        # Build index from real xView metadata if available; fallback to dummy.
        def build():
            if metadata_file.exists():
                stats = index_builder.build_index_from_metadata(
                    metadata_list=index_builder.dataset_loader.load_from_json(str(metadata_file)),
                    image_dir=None,
                    batch_size=10,
                )
            else:
                stats = index_builder.build_dummy_index(num_chips=100, batch_size=10)
            logger.info(f"Index build complete: {stats}")
        
        background_tasks.add_task(build)
        
        return {
            "success": True,
            "message": "Index building started",
            "status": "processing",
            "metadata_file": str(metadata_file),
        }
    
    except Exception as e:
        logger.error(f"Index build error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/index/build-from-dataset")
async def build_index_from_dataset(background_tasks: BackgroundTasks):
    """Preprocess xView dataset and build index from train_images/train_labels."""
    try:
        index_builder = get_index_builder()
        if not index_builder:
            raise HTTPException(status_code=503, detail="Index builder not initialized")

        images_dir = Path(XVIEW_TRAIN_IMAGES_DIR)
        labels_file = Path(XVIEW_TRAIN_LABELS_FILE)
        output_dir = Path(XVIEW_METADATA_FILE).parent

        if not images_dir.exists():
            raise HTTPException(status_code=400, detail=f"Images dir not found: {images_dir}")
        if not labels_file.exists():
            raise HTTPException(status_code=400, detail=f"Labels file not found: {labels_file}")

        def build() -> None:
            from scripts.preprocess_xview import preprocess_xview_dataset

            metadata_path = preprocess_xview_dataset(
                images_dir=images_dir,
                labels_file=labels_file,
                output_dir=output_dir,
                chip_size=XVIEW_CHIP_SIZE,
                overlap=XVIEW_CHIP_OVERLAP,
                max_images=None,
            )

            metadata_list = index_builder.dataset_loader.load_from_json(str(metadata_path))
            stats = index_builder.build_index_from_metadata(
                metadata_list=metadata_list,
                image_dir=None,
                batch_size=10,
            )
            logger.info("Dataset preprocessing + index build complete: %s", stats)

        background_tasks.add_task(build)

        return {
            "success": True,
            "message": "Dataset preprocessing + index build started",
            "status": "processing",
            "images_dir": str(images_dir),
            "labels_file": str(labels_file),
            "metadata_output": str(XVIEW_METADATA_FILE),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Dataset build error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/index/status")
async def index_status():
    """Get index status."""
    try:
        index_builder = get_index_builder()
        if not index_builder:
            raise HTTPException(
                status_code=503,
                detail="Index builder not initialized"
            )
        
        count = index_builder.chroma_service.get_collection_count()
        
        return {
            "success": True,
            "status": {
                "total_embeddings": count,
                "collection_name": index_builder.chroma_service.collection_name
            }
        }
    
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/index/reset")
async def reset_index():
    """Reset index (delete all embeddings)."""
    try:
        index_builder = get_index_builder()
        if not index_builder:
            raise HTTPException(
                status_code=503,
                detail="Index builder not initialized"
            )
        
        index_builder.chroma_service.delete_collection()
        
        return {
            "success": True,
            "message": "Index reset successfully"
        }
    
    except Exception as e:
        logger.error(f"Reset error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
