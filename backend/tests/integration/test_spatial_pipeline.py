"""Integration test for Spatial Engine pipeline with PostGIS database."""

import pytest
from app.db.session import engine, SessionLocal
from scripts.init_db import init_db
from scripts.seed_demo import seed_demo
from app.schemas.plan import AnalysisPlan, SpatialOperation
from app.schemas.query import GeographicScope
from app.services.spatial.engine import SpatialEngine, SpatialResult


def is_db_available() -> bool:
    try:
        with engine.connect() as conn:
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not is_db_available(), reason="PostgreSQL/PostGIS database unavailable"
)


def test_spatial_pipeline_integration():
    # 1. Initialize schema and seed demo data
    init_db()
    seed_demo()

    db = SessionLocal()
    try:
        # 2. Build AnalysisPlan with 3 spatial operations: within, area, count
        plan = AnalysisPlan(
            intent="Analyze health facilities in demo region",
            geographic_scope=GeographicScope(type="demo_default"),
            datasets=["demo_region", "facilities"],
            spatial_operations=[
                SpatialOperation(op="within"),
                SpatialOperation(op="area"),
                SpatialOperation(op="count"),
            ],
            statistics=["region_area_km2", "facility_count"],
            outputs=["geojson", "statistics"]
        )

        # 3. Instantiate SpatialEngine and execute plan
        spatial_engine = SpatialEngine(db)
        result: SpatialResult = spatial_engine.execute(plan)

        # 4. Assert SpatialResult output structure and contents
        assert isinstance(result, SpatialResult)
        assert len(result.operations) == 3

        op_names = [op["op"] for op in result.operations]
        assert op_names == ["within", "area", "count"]

        for op in result.operations:
            assert op["status"] == "ok", f"Operation {op['op']} failed: {op.get('details')}"
            assert "duration_ms" in op

        # 5. Assert statistics
        assert "region_area_km2" in result.statistics
        assert result.statistics["region_area_km2"] > 0, f"Expected region_area_km2 > 0, got {result.statistics['region_area_km2']}"

        assert "facility_count" in result.statistics
        assert result.statistics["facility_count"] == 10, f"Expected facility_count == 10, got {result.statistics['facility_count']}"

        # 6. Assert features is a list of GeoJSON Features
        assert isinstance(result.features, list)
        assert len(result.features) == 10

        for feat in result.features:
            assert feat.get("type") == "Feature"
            assert "geometry" in feat
            assert "properties" in feat
            assert feat["properties"].get("feature_type") == "health_facility"

        # 7. Assert provenance information
        assert isinstance(result.provenance, list)
        assert len(result.provenance) > 0
        assert "demo_region" in result.provenance[0]["datasets"]
        assert result.provenance[0]["srid"] == 4326

    finally:
        db.close()
