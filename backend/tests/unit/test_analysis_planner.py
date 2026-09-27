import pytest
from app.schemas.query import QueryIntent, GeographicScope
from app.schemas.plan import AnalysisPlan, SpatialOperation, CVOperation
from app.services.planning.planner import plan_analysis, deterministic_template
from app.core.errors import GeoMindError, ErrorCode

class DummyAIPlanner:
    def __init__(self, should_fail=False, return_invalid=False):
        self.should_fail = should_fail
        self.return_invalid = return_invalid

    def understand_query(self, question: str, context: dict):
        pass

    def create_analysis_plan(self, intent: QueryIntent, available: dict) -> AnalysisPlan:
        if self.should_fail:
            raise RuntimeError("AI planning timeout")
        if self.return_invalid:
            return "not_a_plan" # type: ignore
        return AnalysisPlan(
            intent=intent.intent,
            geographic_scope=intent.geographic_scope,
            datasets=available.get("datasets", []),
            spatial_operations=[SpatialOperation(op="count")],
            cv_operations=[],
            statistics=["count"],
            outputs=["geojson", "statistics", "insight"]
        )

def test_deterministic_template_accessibility():
    intent = QueryIntent(
        intent="accessibility",
        target="facility",
        geographic_scope=GeographicScope(type="demo_default"),
        analysis_type="spatial_analysis",
        requires_computer_vision=False,
        confidence=0.5,
        raw_question="Healthcare access"
    )
    plan = deterministic_template(intent, ["facilities", "geographic_regions"])
    assert isinstance(plan, AnalysisPlan)
    ops = [op.op for op in plan.spatial_operations]
    assert "within" in ops
    assert "count" in ops

def test_deterministic_template_missing_dataset():
    intent = QueryIntent(
        intent="accessibility",
        target="facility",
        geographic_scope=GeographicScope(type="demo_default"),
        analysis_type="spatial_analysis",
        requires_computer_vision=False,
        confidence=0.5,
        raw_question="Healthcare access"
    )
    with pytest.raises(GeoMindError) as exc_info:
        deterministic_template(intent, ["facilities"]) # missing geographic_regions
    
    assert exc_info.value.code == ErrorCode.DATASET_NOT_FOUND

def test_deterministic_template_change_detection():
    intent = QueryIntent(
        intent="change_detection",
        target="built_up",
        geographic_scope=GeographicScope(type="demo_default"),
        analysis_type="computer_vision",
        requires_computer_vision=True,
        confidence=0.5,
        raw_question="Urban growth"
    )
    plan = deterministic_template(intent, ["geographic_regions"])
    assert len(plan.cv_operations) > 0
    assert plan.cv_operations[0].task == "change_detection"

def test_plan_analysis_ai_success():
    ai = DummyAIPlanner()
    intent = QueryIntent(
        intent="accessibility",
        target="facility",
        geographic_scope=GeographicScope(type="demo_default"),
        analysis_type="spatial_analysis",
        requires_computer_vision=False,
        confidence=0.5,
        raw_question="Healthcare access"
    )
    plan = plan_analysis(intent, ai=ai, available_datasets=["facilities", "geographic_regions"])
    assert isinstance(plan, AnalysisPlan)

def test_plan_analysis_ai_failure_fallback():
    ai = DummyAIPlanner(should_fail=True)
    intent = QueryIntent(
        intent="accessibility",
        target="facility",
        geographic_scope=GeographicScope(type="demo_default"),
        analysis_type="spatial_analysis",
        requires_computer_vision=False,
        confidence=0.5,
        raw_question="Healthcare access"
    )
    plan = plan_analysis(intent, ai=ai, available_datasets=["facilities", "geographic_regions"])
    assert isinstance(plan, AnalysisPlan)
    ops = [op.op for op in plan.spatial_operations]
    assert "within" in ops
