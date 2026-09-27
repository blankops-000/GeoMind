from __future__ import annotations
from typing import Optional, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class ModelMetadata(BaseModel):
    name: str
    version: str
    provider: Optional[str] = None

class VisionInput(BaseModel):
    imagery_ref: str
    task: str
    parameters: dict[str, Any] = {}
    geographic_scope: Optional[dict] = None

class VisionResult(BaseModel):
    analysis_id: Optional[UUID] = None
    task_type: str
    model_name: str
    model_version: str
    source_imagery_id: str
    label: Optional[str] = None
    confidence: Optional[float] = None
    regions: Optional[list[dict]] = None
    image_coords: Optional[list[dict]] = None
    area_km2: Optional[float] = None
    count: Optional[int] = None
    statistics: dict[str, Any] = {}
    processing_metadata: dict[str, Any] = {}
    quality_flags: list[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
