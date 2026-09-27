from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field

class GeographicScope(BaseModel):
    type: Literal["polygon", "named_place", "demo_default"] = "demo_default"
    coordinates: Optional[list] = None
    name: Optional[str] = None

class TimeRange(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None

class QueryIntent(BaseModel):
    intent: str
    target: str
    geographic_scope: GeographicScope
    time_range: Optional[TimeRange] = None
    analysis_type: str
    requires_computer_vision: bool = False
    confidence: float = 0.0
    raw_question: str
