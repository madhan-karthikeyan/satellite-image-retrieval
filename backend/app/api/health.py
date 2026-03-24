from fastapi import APIRouter
from app.schemas.models import HealthResponse
from app.services.embedding import embedding_service
from app.services.chroma import chroma_service
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        embedding_model=settings.EMBEDDING_MODEL,
        chroma_available=True,
        device=str(embedding_service.get_device())
    )


@router.get("/stats")
async def get_stats():
    return {
        "total_chips": chroma_service.count_chips(),
        "object_names": chroma_service.list_object_names(),
        "chroma_dir": str(settings.CHROMA_DIR),
        "embedding_dim": settings.EMBEDDING_DIM
    }
