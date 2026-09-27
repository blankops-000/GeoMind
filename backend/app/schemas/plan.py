from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel
from app.schemas.query import GeographicScope, TimeRange

class SpatialOperation(BaseModel):
    op: Literal[
        "intersection", "within", "dwithin", "buffer",
        "area", "count", "aggregate", "distance"
    ]

class CVOperation(BaseModel):
    task: Literal[
        "classification", "segmentation",
        "detection", "change_detection"
    ]
    target_feature: str
    imagery_source: str
    time_range: Optional[TimeRange] = None

class AnalysisPlan(BaseModel):
    intent: str
    geographic_scope: GeographicScope
    datasets: list[str]
    spatial_operations: list[SpatialOperation] = []
    cv_operations: list[CVOperation] = []
    statistics: list[str] = []
    outputs: list[Literal["geojson", "statistics", "insight"]] = [
        "geojson", "statistics", "insight"
    ]
