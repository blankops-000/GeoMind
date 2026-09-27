import pytest
from app.db.session import engine, SessionLocal
from app.db.repositories.datasets import DatasetRepository
from app.db.repositories.regions import RegionRepository
from app.db.repositories.facilities import FacilityRepository
from app.db.repositories.analysis import AnalysisRepository
from app.db.repositories.vision import VisionRepository


def is_db_available():
    try:
        with engine.connect() as conn:
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not is_db_available(), reason="PostgreSQL/PostGIS database unavailable"
)


def test_dataset_repository_roundtrip():
    db = SessionLocal()
    try:
        repo = DatasetRepository(db)
        test_name = f"test_ds_{pytest.importorskip('uuid').uuid4().hex[:8]}"
        ds_id = repo.create(
            name=test_name,
            source="unit_test",
            description="Unit test dataset",
        )
        assert ds_id is not None
        fetched = repo.get_by_name(test_name)
        assert fetched is not None
        assert fetched["name"] == test_name
        assert fetched["source"] == "unit_test"

        all_ds = repo.list_all()
        assert any(d["name"] == test_name for d in all_ds)
    finally:
        db.close()


def test_region_repository_find_containing():
    db = SessionLocal()
    try:
        repo = RegionRepository(db)
        # Check if Demo Region exists or search around center of DEMO_BBOX
        all_regions = repo.list_all()
        if len(all_regions) > 0:
            reg = repo.find_containing(-1.3, 36.75)
            assert reg is None or isinstance(reg, dict)
    finally:
        db.close()
