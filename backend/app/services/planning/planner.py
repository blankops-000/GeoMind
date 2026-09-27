from __future__ import annotations
import logging
from typing import Protocol, Optional, Any, List
from app.schemas.query import QueryIntent
from app.schemas.plan import AnalysisPlan, SpatialOperation, CVOperation
from app.core.errors import GeoMindError, ErrorCode

logger = logging.getLogger(__name__)

class AIProvider(Protocol):
    def understand_query(self, question: str, context: dict) -> Any: ...
    def create_analysis_plan(self, intent: QueryIntent, available: dict) -> AnalysisPlan: ...

def plan_analysis(
    intent: QueryIntent,
    ai: AIProvider | None,
    available_datasets: list[str]
) -> AnalysisPlan:
    """
    Convert QueryIntent -> AnalysisPlan.
    Try AI planner; fall back to deterministic template.
    Always returns a valid AnalysisPlan.
    """
    if ai is not None:
        try:
            plan = ai.create_analysis_plan(intent, {"datasets": available_datasets})
            if not isinstance(plan, AnalysisPlan):
                raise ValueError(f"AI returned invalid plan type: {type(plan)}")
            return plan
        except Exception as exc:
            logger.warning(f"AI planning failed, using deterministic template: {exc}")

    return deterministic_template(intent, available_datasets)

def deterministic_template(
    intent: QueryIntent,
    available_datasets: list[str]
) -> AnalysisPlan:
    """
    Generate a deterministic AnalysisPlan based on QueryIntent.
    Raises GeoMindError(code=DATASET_NOT_FOUND) if a required dataset is missing.
    """
    intent_name = intent.intent.lower() if intent.intent else "accessibility"

    if intent_name == "accessibility":
        required_datasets = ["facilities", "geographic_regions"]
        spatial_ops = [
            SpatialOperation(op="within"),
            SpatialOperation(op="count"),
            SpatialOperation(op="dwithin"),
            SpatialOperation(op="distance"),
            SpatialOperation(op="area"),
        ]
        cv_ops: list[CVOperation] = []
        stats = ["facility_count", "region_area_km2", "avg_facility_distance_to_point"]

    elif intent_name == "change_detection":
        required_datasets = ["geographic_regions"]
        spatial_ops = [
            SpatialOperation(op="intersection"),
            SpatialOperation(op="area"),
        ]
        cv_ops = [
            CVOperation(
                task="change_detection",
                target_feature="built_up",
                imagery_source="sentinel2"
            )
        ]
        stats = ["change_area_km2", "change_percent"]

    elif intent_name == "land_cover":
        required_datasets = ["geographic_regions"]
        spatial_ops = [
            SpatialOperation(op="intersection"),
            SpatialOperation(op="area"),
        ]
        cv_ops = [
            CVOperation(
                task="segmentation",
                target_feature="vegetation",
                imagery_source="sentinel2"
            )
        ]
        stats = ["vegetation_area_km2", "vegetation_percent"]

    elif intent_name == "proximity":
        required_datasets = ["facilities", "geographic_regions"]
        spatial_ops = [
            SpatialOperation(op="dwithin"),
            SpatialOperation(op="distance"),
            SpatialOperation(op="count"),
        ]
        cv_ops = []
        stats = ["avg_distance_m", "within_count"]

    else:
        # Default fallback template: accessibility
        required_datasets = ["facilities", "geographic_regions"]
        spatial_ops = [
            SpatialOperation(op="within"),
            SpatialOperation(op="count"),
            SpatialOperation(op="dwithin"),
            SpatialOperation(op="distance"),
            SpatialOperation(op="area"),
        ]
        cv_ops = []
        stats = ["facility_count", "region_area_km2", "avg_facility_distance_to_point"]

    # Validate dataset availability
    missing = [ds for ds in required_datasets if ds not in available_datasets]
    if missing:
        raise GeoMindError(
            code=ErrorCode.DATASET_NOT_FOUND,
            message=f"Required dataset(s) {missing} not found in available datasets: {available_datasets}"
        )

    return AnalysisPlan(
        intent=intent.intent,
        geographic_scope=intent.geographic_scope,
        datasets=required_datasets,
        spatial_operations=spatial_ops,
        cv_operations=cv_ops,
        statistics=stats,
        outputs=["geojson", "statistics", "insight"],
    )
