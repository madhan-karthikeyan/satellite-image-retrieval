from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SearchResult(BaseModel):
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    searched_object_name: str
    target_imagery_file_name: str
    similarity_score: float


class SearchRequest(BaseModel):
    object_name: str = Field(..., description="Name of the object/feature to search")
    target_directory: str = Field(..., description="Path to satellite imagery directory")
    output_directory: str = Field(..., description="Path for output files")
    similarity_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    batch_name: Optional[str] = Field(default=None, description="Team/batch name for output file")


class SearchResponse(BaseModel):
    success: bool
    message: str
    results_count: int
    results: List[SearchResult]
    output_file: Optional[str] = None
    processing_time_seconds: float


class ImageChipInfo(BaseModel):
    id: str
    filename: str
    object_name: str
    width: int
    height: int
    channels: int
    uploaded_at: datetime


class ChipUploadResponse(BaseModel):
    success: bool
    message: str
    chip_id: str
    chip_info: ImageChipInfo


class ImageryInfo(BaseModel):
    filename: str
    width: int
    height: int
    bands: int
    format: str


class ImageryListResponse(BaseModel):
    success: bool
    imagery_count: int
    imagery_list: List[ImageryInfo]


class HealthResponse(BaseModel):
    status: str
    embedding_model: str
    chroma_available: bool
    device: str
