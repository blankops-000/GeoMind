import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.db.session import SessionLocal


def is_db_available():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception:
        return False


db_available = is_db_available()
pytestmark = pytest.mark.skipif(
    not db_available, reason="Database is not available"
)

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "database" in data
    assert "ai" in data
    assert "version" in data


def test_datasets_endpoint():
    res = client.get("/api/v1/datasets")
    assert res.status_code == 200
    data = res.json()
    assert "datasets" in data
    assert isinstance(data["datasets"], list)


def test_query_and_analysis_flow():
    post_res = client.post(
        "/api/v1/query",
        json={"question": "Find flood risk zones in Nairobi"},
    )
    assert post_res.status_code == 202
    post_data = post_res.json()
    assert "analysis_id" in post_data
    assert post_data["status"] == "processing"
    analysis_id = post_data["analysis_id"]

    get_res = client.get(f"/api/v1/analysis/{analysis_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["analysis_id"] == analysis_id
    assert get_data["status"] in ("processing", "completed", "failed")


def test_analysis_not_found():
    random_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/analysis/{random_id}")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data


def test_query_validation_error():
    res = client.post("/api/v1/query", json={"question": "a"})
    assert res.status_code == 422
