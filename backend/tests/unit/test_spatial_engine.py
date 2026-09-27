"""Unit tests for Spatial Engine and Spatial Operations."""

import pytest
from unittest.mock import MagicMock
from shapely.geometry import Polygon

from app.schemas.plan import AnalysisPlan, SpatialOperation
from app.schemas.query import GeographicScope
from app.core.errors import GeoMindError, ErrorCode
from app.services.spatial.engine import SpatialEngine, SpatialResult, SUPPORTED_SPATIAL_OPS
from app.services.spatial.statistics import density_per_km2
from app.services.spatial.geopandas_ops import polygonize_mask, simplify_features, merge_adjacent_polygons
import numpy as np


def test_supported_spatial_ops_completeness():
    expected_ops = {"intersection", "within", "dwithin", "buffer", "area", "count", "aggregate", "distance"}
    assert SUPPORTED_SPATIAL_OPS == expected_ops


def test_unsupported_operation_raises_geomind_error():
    db_mock = MagicMock()
    engine = SpatialEngine(db_mock)
    plan = AnalysisPlan(
        intent="test",
        geographic_scope=GeographicScope(type="demo_default"),
        datasets=["facilities"],
        spatial_operations=[SpatialOperation(op="within")]
    )
    # Inject unsupported op
    plan.spatial_operations[0].op = "unsupported_magic_op"

    with pytest.raises(GeoMindError) as excinfo:
        engine.execute(plan)

    assert excinfo.value.code == ErrorCode.UNSUPPORTED_ANALYSIS


def test_density_per_km2():
    assert density_per_km2(10, 2.0) == 5.0
    assert density_per_km2(10, 0.0) == 0.0
    assert density_per_km2(0, 5.0) == 0.0


def test_geopandas_ops():
    # 1. merge_adjacent_polygons
    p1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    p2 = Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])
    merged = merge_adjacent_polygons([p1, p2])
    assert merged.area == pytest.approx(2.0)

    # 2. simplify_features
    features = [{
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 0.0001], [1, 1], [0, 1], [0, 0]]]
        },
        "properties": {"test": "val"}
    }]
    simp = simplify_features(features, tolerance=0.01)
    assert len(simp) == 1
    assert simp[0]["properties"]["test"] == "val"

    # 3. polygonize_mask
    mask = np.array([[1, 0], [0, 1]], dtype=bool)
    polys = polygonize_mask(mask)
    assert len(polys) >= 1


def test_op_area_calculation_unit():
    db_mock = MagicMock()
    # Mock db.execute for ST_Area returning 10.5 km2
    mock_scalar = MagicMock()
    mock_scalar.scalar.return_value = 10.5
    db_mock.execute.return_value = mock_scalar

    engine = SpatialEngine(db_mock)
    poly = Polygon([(36.5, -1.5), (37.0, -1.5), (37.0, -1.1), (36.5, -1.1)])
    op_res, feats, funcs = engine._op_area(poly, '{"type": "Polygon"}')

    assert op_res["op"] == "area"
    assert op_res["status"] == "ok"
    assert op_res["details"]["area_km2"] == 10.5
    assert "ST_Area" in funcs


def test_op_count_unit():
    db_mock = MagicMock()
    mock_scalar = MagicMock()
    mock_scalar.scalar.return_value = 7
    db_mock.execute.return_value = mock_scalar

    engine = SpatialEngine(db_mock)
    poly = Polygon([(36.5, -1.5), (37.0, -1.5), (37.0, -1.1), (36.5, -1.1)])
    op_res, feats, funcs = engine._op_count(poly, '{"type": "Polygon"}')

    assert op_res["op"] == "count"
    assert op_res["status"] == "ok"
    assert op_res["details"]["count"] == 7
    assert op_res["result_count"] == 7
