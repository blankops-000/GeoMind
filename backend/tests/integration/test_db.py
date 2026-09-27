import pytest
from app.db.session import engine, SessionLocal
from scripts.init_db import init_db
from scripts.seed_demo import seed_demo
from app.db.repositories.regions import RegionRepository
from app.db.repositories.facilities import FacilityRepository
from app.db.spatial_queries import facilities_within_region, region_area_km2


def is_db_available():
    try:
        with engine.connect() as conn:
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not is_db_available(), reason="PostgreSQL/PostGIS database unavailable"
)


def test_db_init_and_seed_integration():
    # 1. Run init_db and seed_demo
    init_db()
    seed_demo()

    db = SessionLocal()
    try:
        # 2. Assert region exists
        region_repo = RegionRepository(db)
        regions = region_repo.list_all()
        demo_region = next((r for r in regions if r["name"] == "Demo Region"), None)
        assert demo_region is not None, "Demo Region should exist"

        # 3. Assert facilities exist
        facility_repo = FacilityRepository(db)
        counts = facility_repo.count_by_type()
        total_facilities = sum(c["count"] for c in counts if c["feature_type"] == "health_facility")
        assert total_facilities == 10, f"Expected 10 health facilities, found {total_facilities}"

        # 4. Assert facilities_within_region returns 10
        region_facilities = facilities_within_region(db, demo_region["id"])
        assert len(region_facilities) == 10, f"Expected 10 facilities within region, got {len(region_facilities)}"

        # 5. Assert region_area_km2 > 0
        area = region_area_km2(db, demo_region["id"])
        assert area > 0, f"Expected area > 0, got {area}"

    finally:
        db.close()
