import pytest
from app.schemas.query import GeographicScope
from app.schemas.plan import AnalysisPlan, SpatialOperation, CVOperation
from app.services.planning.validator import validate_plan
from app.core.errors import GeoMindError, ErrorCode

def test_validate_plan_valid():
    plan = AnalysisPlan(
        intent="accessibility",
        geographic_scope=GeographicScope(type="demo_default"),
        datasets=["facilities"],
        spatial_operations=[SpatialOperation(op="within")],
        cv_operations=[],
        statistics=["count"],
        outputs=["geojson", "statistics"]
    )
    result = validate_plan(plan, ["facilities", "geographic_regions"])
    assert result == plan

def test_validate_plan_empty_intent():
    plan = AnalysisPlan(
        intent="",
        geographic_scope=GeographicScope(type="demo_default"),
        datasets=["facilities"],
        spatial_operations=[SpatialOperation(op="within")],
    )
    with pytest.raises(GeoMindError) as exc_info:
        validate_plan(plan, ["facilities"])
    assert exc_info.value.code == ErrorCode.INVALID_QUERY

def test_validate_plan_unknown_dataset():
    plan = AnalysisPlan(
        intent="accessibility",
        geographic_scope=GeographicScope(type="demo_default"),
        datasets=["secret_dataset"],
        spatial_operations=[SpatialOperation(op="within")],
    )
    with pytest.raises(GeoMindError) as exc_info:
        validate_plan(plan, ["facilities"])
    assert exc_info.value.code == ErrorCode.DATASET_NOT_FOUND

def test_validate_plan_unknown_spatial_op():
    plan = AnalysisPlan(
        intent="accessibility",
        geographic_scope=GeographicScope(type="demo_default"),
        datasets=["facilities"],
        spatial_operations=[SpatialOperation.model_construct(op="super_teleport")], # type: ignore
    )
    with pytest.raises(GeoMindError) as exc_info:
        validate_plan(plan, ["facilities"])
    assert exc_info.value.code == ErrorCode.UNSUPPORTED_ANALYSIS

def test_validate_plan_unknown_cv_task():
    plan = AnalysisPlan(
        intent="accessibility",
        geographic_scope=GeographicScope(type="demo_default"),
        datasets=["facilities"],
        cv_operations=[CVOperation.model_construct(task="xray_scan", target_feature="x", imagery_source="y")], # type: ignore
    )
    with pytest.raises(GeoMindError) as exc_info:
        validate_plan(plan, ["facilities"])
    assert exc_info.value.code == ErrorCode.UNSUPPORTED_ANALYSIS

def test_validate_plan_unknown_scope_type():
    plan = AnalysisPlan(
        intent="accessibility",
        geographic_scope=GeographicScope.model_construct(type="mars_surface"), # type: ignore
        datasets=["facilities"],
    )
    with pytest.raises(GeoMindError) as exc_info:
        validate_plan(plan, ["facilities"])
    assert exc_info.value.code == ErrorCode.INVALID_QUERY

def test_validate_plan_polygon_missing_coords():
    plan = AnalysisPlan(
        intent="accessibility",
        geographic_scope=GeographicScope(type="polygon", coordinates=[]),
        datasets=["facilities"],
    )
    with pytest.raises(GeoMindError) as exc_info:
        validate_plan(plan, ["facilities"])
    assert exc_info.value.code == ErrorCode.INVALID_GEOMETRY

def test_validate_plan_polygon_excessive_vertices():
    too_many_vertices = [[i, i] for i in range(1500)]
    plan = AnalysisPlan(
        intent="accessibility",
        geographic_scope=GeographicScope(type="polygon", coordinates=too_many_vertices),
        datasets=["facilities"],
    )
    with pytest.raises(GeoMindError) as exc_info:
        validate_plan(plan, ["facilities"])
    assert exc_info.value.code == ErrorCode.INVALID_GEOMETRY
