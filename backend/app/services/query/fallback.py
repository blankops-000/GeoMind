from __future__ import annotations
from typing import Optional
from app.schemas.query import QueryIntent, GeographicScope, TimeRange

ACCESSIBILITY_KEYWORDS = [
    "access", "accessibility", "healthcare",
    "health facility", "hospital", "clinic",
    "underserved", "coverage"
]
CHANGE_KEYWORDS = [
    "change", "growth", "expansion",
    "development", "built-up", "urban"
]
LAND_COVER_KEYWORDS = [
    "land cover", "vegetation", "forest",
    "land use", "green"
]
PROXIMITY_KEYWORDS = [
    "near", "close", "distance", "within",
    "far", "proximity"
]

def parse_question(question: str) -> QueryIntent:
    """
    Deterministic keyword parser for query understanding.
    Always returns a valid QueryIntent. Never raises.
    """
    if not isinstance(question, str):
        question = str(question or "")

    q_lower = question.lower()

    # Determine intent group
    intent_type = None
    target = "facility"
    analysis_type = "spatial_analysis"
    requires_cv = False
    confidence = 0.5

    if any(kw in q_lower for kw in ACCESSIBILITY_KEYWORDS):
        intent_type = "accessibility"
        target = "health_facility"
        analysis_type = "spatial_analysis"
        requires_cv = False
        confidence = 0.5
    elif any(kw in q_lower for kw in CHANGE_KEYWORDS):
        intent_type = "change_detection"
        target = "built_up_area"
        analysis_type = "computer_vision"
        requires_cv = True
        confidence = 0.5
    elif any(kw in q_lower for kw in LAND_COVER_KEYWORDS):
        intent_type = "land_cover"
        target = "vegetation"
        analysis_type = "computer_vision"
        requires_cv = True
        confidence = 0.5
    elif any(kw in q_lower for kw in PROXIMITY_KEYWORDS):
        intent_type = "proximity"
        target = "facility"
        analysis_type = "spatial_analysis"
        requires_cv = False
        confidence = 0.5
    else:
        intent_type = "accessibility"
        target = "facility"
        analysis_type = "spatial_analysis"
        requires_cv = False
        confidence = 0.3

    # Geographic Scope parsing
    if "nairobi" in q_lower:
        scope = GeographicScope(type="named_place", name="Nairobi")
    elif "kenya" in q_lower:
        scope = GeographicScope(type="named_place", name="Kenya")
    else:
        scope = GeographicScope(type="demo_default")

    return QueryIntent(
        intent=intent_type,
        target=target,
        geographic_scope=scope,
        time_range=None,
        analysis_type=analysis_type,
        requires_computer_vision=requires_cv,
        confidence=confidence,
        raw_question=question,
    )
