"""Pydantic response models for the API."""

from typing import Optional
from pydantic import BaseModel, Field


class SecondaryCluster(BaseModel):
    """Secondary cluster information."""

    centroid_lat: float = Field(..., description="Centroid latitude")
    centroid_lon: float = Field(..., description="Centroid longitude")
    size: int = Field(..., description="Number of points in cluster")


class SimilarityStats(BaseModel):
    """Statistics about similarity scores in the cluster."""

    mean: float = Field(..., description="Mean similarity score")
    min: float = Field(..., description="Minimum similarity score")
    max: float = Field(..., description="Maximum similarity score")
    std: float = Field(..., description="Standard deviation of similarity scores")
    q25: float = Field(..., description="25th percentile similarity")
    q75: float = Field(..., description="75th percentile similarity")


class InferenceResponse(BaseModel):
    """Successful inference response."""

    status: str = Field(default="success", description="Status of inference")
    centroid_lat: float = Field(..., description="Predicted latitude")
    centroid_lon: float = Field(..., description="Predicted longitude")
    confidence_radius_km: float = Field(..., description="Confidence radius in km")
    confidence_level: str = Field(..., description="Confidence level: high, medium, or low")
    cluster_size: int = Field(..., description="Number of images in cluster")
    total_candidates: int = Field(..., description="Total candidates retrieved")
    scene_distribution: dict[str, int] = Field(..., description="Scene category distribution")
    secondary_clusters: list[SecondaryCluster] = Field(default_factory=list, description="Secondary clusters")
    similarity_stats: Optional[SimilarityStats] = Field(None, description="Similarity score statistics")
    explanation: Optional[str] = Field(None, description="Natural language explanation")
    country: Optional[str] = Field(None, description="Predicted country")
    country_code: Optional[str] = Field(None, description="ISO country code")
    region: Optional[str] = Field(None, description="State/region")
    city: Optional[str] = Field(None, description="City name")
    continent: Optional[str] = Field(None, description="Continent")


class InsufficientConfidenceResponse(BaseModel):
    """Response when inference fails due to low confidence."""

    status: str = Field(default="insufficient_confidence", description="Status of inference")
    message: str = Field(..., description="Error message")
    candidates_retrieved: int = Field(..., description="Number of candidates retrieved")


class IndexStatsResponse(BaseModel):
    """Index statistics response."""

    collection_size: int = Field(..., description="Number of embeddings in collection")
    collection_name: str = Field(default="fmow_embeddings", description="Collection name")


class BuildIndexResponse(BaseModel):
    """Build index response."""

    status: str = Field(..., description="Status of indexing operation")
    message: str = Field(..., description="Status message")
    total_indexed: int = Field(..., description="Total number of indexed items")


class ErrorResponse(BaseModel):
    """Error response."""

    status: str = Field(default="error", description="Status of error")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
