import time
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _db_available() -> bool:
    from app.db.session import SessionLocal
    from sqlalchemy import text

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _db_available(),
    reason="Database not available for E2E test",
)


def test_health_endpoint():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_datasets_endpoint():
    r = client.get("/api/v1/datasets")
    assert r.status_code == 200
    assert "datasets" in r.json()
    assert isinstance(r.json()["datasets"], list)


def test_full_analysis_flow():
    # 1. Submit query
    r = client.post(
        "/api/v1/query",
        json={"question": "Which areas have limited healthcare access?"},
    )
    assert r.status_code == 202
    body = r.json()
    assert "analysis_id" in body
    analysis_id = body["analysis_id"]

    # 2. Poll until completed or failed (max 30 s)
    final = None
    for _ in range(30):
        s = client.get(f"/api/v1/analysis/{analysis_id}")
        assert s.status_code == 200
        payload = s.json()
        if payload["status"] in ("completed", "failed"):
            final = payload
            break
        time.sleep(1)

    assert final is not None, "Analysis did not complete in time"
    assert final["status"] == "completed", f"Analysis failed: {final}"

    # 3. Validate the completed payload shape
    assert final["analysis_id"] == analysis_id
    assert "map" in final
    assert final["map"]["type"] == "FeatureCollection"
    assert "features" in final["map"]
    assert isinstance(final["map"]["features"], list)

    assert "statistics" in final
    assert isinstance(final["statistics"], dict)

    assert "insight" in final
    insight = final["insight"]
    assert insight is not None
    assert "headline" in insight
    assert isinstance(insight["headline"], str)
    assert len(insight["headline"]) > 0
    assert "summary" in insight
    assert "key_findings" in insight
    assert isinstance(insight["key_findings"], list)

    assert "provenance" in final
    assert isinstance(final["provenance"], list)

    assert "limitations" in final
    assert isinstance(final["limitations"], list)


def test_unknown_analysis_returns_404():
    fake_id = str(uuid4())
    r = client.get(f"/api/v1/analysis/{fake_id}")
    assert r.status_code == 404
    body = r.json()
    assert "error" in body
    assert "code" in body["error"]


def test_query_validation_rejects_empty_question():
    r = client.post("/api/v1/query", json={"question": ""})
    assert r.status_code == 422
