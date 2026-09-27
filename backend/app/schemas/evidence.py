from __future__ import annotations
from typing import Optional, Any, Literal
from uuid import UUID
from pydantic import BaseModel

class EvidenceItem(BaseModel):
    evidence_type: Literal["spatial", "cv", "statistic", "dataset"]
    description: str
    value: Optional[float | int | str] = None
    unit: Optional[str] = None
    geometry: Optional[dict] = None
    source: str
    confidence: Optional[float] = None
    metadata: dict[str, Any] = {}

class EvidencePackage(BaseModel):
    analysis_id: UUID
    area: str
    datasets: list[str] = []
    spatial_results: dict[str, Any] = {}
    computer_vision: Optional[dict[str, Any]] = None
    statistics: dict[str, Any] = {}
    geographic_features: list[dict] = []
    evidence_items: list[EvidenceItem] = []
    confidence: dict[str, Any] = {}
    provenance: list[dict] = []
    limitations: list[str] = []
    quality_flags: list[str] = []
