import pytest
from app.services.analysis.state import AnalysisState, TRANSITIONS, can_transition
from app.core.constants import PROGRESS_MAP
from app.services.analysis.orchestrator import AnalysisOrchestrator


def test_can_transition_valid():
    assert can_transition(AnalysisState.CREATED, AnalysisState.UNDERSTANDING)
    assert can_transition("created", "understanding")
    assert can_transition(AnalysisState.UNDERSTANDING, AnalysisState.PLANNING)
    assert can_transition(AnalysisState.UNDERSTANDING, AnalysisState.FAILED)
    assert can_transition(AnalysisState.SPATIAL_ANALYSIS, AnalysisState.COMPUTER_VISION)
    assert can_transition(AnalysisState.SPATIAL_ANALYSIS, AnalysisState.EVIDENCE_BUILDING)
    assert can_transition(AnalysisState.VALIDATION, AnalysisState.COMPLETED)


def test_can_transition_invalid():
    assert not can_transition(AnalysisState.CREATED, AnalysisState.COMPLETED)
    assert not can_transition("created", "ai_reasoning")
    assert not can_transition(AnalysisState.COMPLETED, AnalysisState.CREATED)
    assert not can_transition(AnalysisState.FAILED, AnalysisState.PLANNING)
    assert not can_transition("invalid_state", "created")


def test_progress_map_covers_all_states():
    for state in AnalysisState:
        assert state.value in PROGRESS_MAP, f"State {state.value} missing from PROGRESS_MAP"
        assert isinstance(PROGRESS_MAP[state.value], int)
        assert 0 <= PROGRESS_MAP[state.value] <= 100


def test_orchestrator_initialization():
    orchestrator = AnalysisOrchestrator(db=None)
    assert orchestrator.db is None
    assert orchestrator.ai is None
    assert orchestrator.repo is not None


def test_orchestrator_run_mocked():
    from uuid import uuid4
    from unittest.mock import MagicMock, patch
    from app.services.spatial.engine import SpatialResult
    from app.schemas.result import AnalysisResult

    mock_db = MagicMock()
    orchestrator = AnalysisOrchestrator(db=mock_db)

    # Mock AnalysisRepository methods
    orchestrator.repo.create_run = MagicMock()
    orchestrator.repo.update_status = MagicMock()
    orchestrator.repo.set_intent = MagicMock()
    orchestrator.repo.set_plan = MagicMock()
    orchestrator.repo.save_result = MagicMock()
    orchestrator.repo.mark_completed = MagicMock()

    # Mock DatasetRepository
    mock_ds_repo = MagicMock()
    mock_ds_repo.list_all.return_value = [
        {"name": "facilities"},
        {"name": "geographic_regions"},
    ]

    # Mock SpatialEngine
    mock_spatial_result = SpatialResult(
        operations=[{"op": "within", "status": "ok", "result_count": 5, "duration_ms": 10}],
        statistics={"facility_count": 5},
        features=[{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [36.8, -1.28]},
            "properties": {"feature_type": "hospital"},
        }],
        provenance=[{"datasets": ["facilities"], "srid": 4326}],
    )
    mock_spatial_engine = MagicMock()
    mock_spatial_engine.execute.return_value = mock_spatial_result

    analysis_id = uuid4()
    question = "How many health facilities are in Nairobi?"

    with patch("app.db.repositories.datasets.DatasetRepository", return_value=mock_ds_repo), \
         patch("app.services.spatial.engine.SpatialEngine", return_value=mock_spatial_engine):
        result = orchestrator.run(analysis_id, question)

    assert isinstance(result, AnalysisResult)
    assert result.status == "completed"
    assert result.map["type"] == "FeatureCollection"
    assert len(result.map["features"]) == 1
    assert result.insight is not None
    assert len(result.insight.headline) > 0

    orchestrator.repo.create_run.assert_called_once_with(analysis_id, question)
    orchestrator.repo.save_result.assert_called_once()
    orchestrator.repo.mark_completed.assert_called_once_with(analysis_id)


def test_orchestrator_run_failure_marks_failed():
    from uuid import uuid4
    from unittest.mock import MagicMock, patch
    from app.core.errors import GeoMindError, ErrorCode

    mock_db = MagicMock()
    orchestrator = AnalysisOrchestrator(db=mock_db)

    orchestrator.repo.create_run = MagicMock()
    orchestrator.repo.mark_failed = MagicMock()

    analysis_id = uuid4()

    with patch("app.services.query.understanding.understand_question", side_effect=ValueError("Test error")):
        with pytest.raises(GeoMindError) as exc_info:
            orchestrator.run(analysis_id, "Failing question")

        assert exc_info.value.code == ErrorCode.ANALYSIS_FAILED
        orchestrator.repo.mark_failed.assert_called_once()


