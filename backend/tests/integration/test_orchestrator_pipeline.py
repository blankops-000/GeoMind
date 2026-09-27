import uuid
import pytest
from app.db.session import engine, SessionLocal
from app.db.repositories.analysis import AnalysisRepository
from app.services.analysis.jobs import run_analysis_job
from scripts.init_db import init_db
from scripts.seed_demo import seed_demo


def is_db_available() -> bool:
    try:
        with engine.connect() as conn:
            return True
    except Exception:
        return False


def is_4a_available() -> bool:
    try:
        from app.services.ai.service import AIService
        from app.services.evidence.builder import build_evidence_package
        from app.services.evidence.validator import EvidenceValidator
        return True
    except Exception:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not (is_db_available() and is_4a_available()),
        reason="Database or Agent 4A services unavailable",
    ),
]


def test_orchestrator_pipeline_end_to_end():
    # 1. Initialize schema and seed demo data
    init_db()
    seed_demo()

    db = SessionLocal()
    try:
        analysis_id = uuid.uuid4()
        question = "Analyze health facilities and region boundaries in demo area"

        # 2. Run the full background job pipeline
        run_analysis_job(analysis_id, question)

        # 3. Assert analysis_runs table record
        repo = AnalysisRepository(db)
        run_info = repo.get_run(analysis_id)
        assert run_info is not None
        assert run_info["status"] in ("completed", "COMPLETED")
        assert run_info["progress"] == 100

        # 4. Assert analysis_results table record
        result_info = repo.get_result(analysis_id)
        assert result_info is not None
        assert "geojson" in result_info or "map" in result_info

        geojson_data = result_info.get("geojson")
        assert geojson_data is not None
        assert geojson_data.get("type") == "FeatureCollection"

        insight = result_info.get("insight")
        assert insight is not None
        headline = insight.get("headline") if isinstance(insight, dict) else getattr(insight, "headline", "")
        assert headline and len(headline) > 0

    finally:
        db.close()
