from __future__ import annotations
from typing import Optional, Any, Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class Statistic(BaseModel):
    name: str
    value: float | int | str
    unit: Optional[str] = None

class Finding(BaseModel):
    title: str
    description: str
    confidence: Optional[float] = None

class Insight(BaseModel):
    headline: str
    summary: str
    key_findings: list[str] = []
    confidence: str = "medium"

class AnalysisResult(BaseModel):
    analysis_id: UUID
    status: Literal[
        "created", "processing", "completed", "failed"
    ] = "created"
    query: Optional[dict] = None
    map: Optional[dict] = None
    statistics: dict[str, Any] = {}
    findings: list[Finding] = []
    insight: Optional[Insight] = None
    provenance: list[dict] = []
    confidence: dict[str, Any] = {}
    limitations: list[str] = []
    error: Optional[dict] = None
