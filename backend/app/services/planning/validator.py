from __future__ import annotations
import logging
from typing import Any, List
from app.schemas.plan import AnalysisPlan
from app.core.constants import SUPPORTED_SPATIAL_OPS, SUPPORTED_CV_TASKS
from app.core.errors import GeoMindError, ErrorCode
from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_OUTPUTS = {"geojson", "statistics", "insight"}
ALLOWED_SCOPE_TYPES = {"polygon", "named_place", "demo_default"}

def _count_vertices(coords: Any) -> int:
    if not isinstance(coords, list) or not coords:
        return 0
    first = coords[0]
    if isinstance(first, list):
        if first and isinstance(first[0], (int, float)):
            return len(coords)
        elif first and isinstance(first[0], list):
            total = 0
            for ring in coords:
                if isinstance(ring, list):
                    total += len(ring)
            return total
    return len(coords)

def validate_plan(
    plan: AnalysisPlan,
    available_datasets: list[str]
) -> AnalysisPlan:
    """
    Deterministic allow-list validation.
    Raises GeoMindError on any violation.
    Returns the exact plan if valid.
    """
    # 1. Intent validation
    if not plan.intent or not isinstance(plan.intent, str) or not plan.intent.strip():
        raise GeoMindError(
            code=ErrorCode.INVALID_QUERY,
            message="Plan intent must be a non-empty string"
        )

    # 2. Datasets validation
    for ds in plan.datasets:
        if ds not in available_datasets:
            raise GeoMindError(
                code=ErrorCode.DATASET_NOT_FOUND,
                message=f"Dataset '{ds}' is not available in: {available_datasets}"
            )

    # 3. Spatial operations validation
    for op_item in plan.spatial_operations:
        if op_item.op not in SUPPORTED_SPATIAL_OPS:
            raise GeoMindError(
                code=ErrorCode.UNSUPPORTED_ANALYSIS,
                message=f"Unsupported spatial operation: '{op_item.op}'"
            )

    # 4. CV operations validation
    for cv_item in plan.cv_operations:
        if cv_item.task not in SUPPORTED_CV_TASKS:
            raise GeoMindError(
                code=ErrorCode.UNSUPPORTED_ANALYSIS,
                message=f"Unsupported CV task: '{cv_item.task}'"
            )

    # 5. Outputs validation
    for out in plan.outputs:
        if out not in ALLOWED_OUTPUTS:
            raise GeoMindError(
                code=ErrorCode.UNSUPPORTED_ANALYSIS,
                message=f"Unsupported output format: '{out}'"
            )

    # 6. Geographic scope type validation
    scope = plan.geographic_scope
    if scope.type not in ALLOWED_SCOPE_TYPES:
        raise GeoMindError(
            code=ErrorCode.INVALID_QUERY,
            message=f"Invalid geographic scope type: '{scope.type}'"
        )

    # 7. Polygon coordinates validation
    if scope.type == "polygon":
        if not scope.coordinates or not isinstance(scope.coordinates, list) or len(scope.coordinates) == 0:
            raise GeoMindError(
                code=ErrorCode.INVALID_GEOMETRY,
                message="Polygon scope requires a non-empty coordinates list"
            )
        
        max_vertices = getattr(settings, "MAX_POLYGON_VERTICES", 1000)
        v_count = _count_vertices(scope.coordinates)
        if v_count > max_vertices:
            raise GeoMindError(
                code=ErrorCode.INVALID_GEOMETRY,
                message=f"Polygon vertex count ({v_count}) exceeds maximum allowed ({max_vertices})"
            )

    return plan
