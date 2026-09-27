import pytest
from app.schemas.query import QueryIntent, GeographicScope
from app.services.query.fallback import parse_question
from app.services.query.understanding import understand_question

class DummyAIProvider:
    def __init__(self, should_fail=False, return_invalid=False):
        self.should_fail = should_fail
        self.return_invalid = return_invalid

    def understand_query(self, question: str, context: dict) -> QueryIntent:
        if self.should_fail:
            raise RuntimeError("AI model timeout")
        if self.return_invalid:
            return "not_a_query_intent" # type: ignore
        return QueryIntent(
            intent="custom_ai_intent",
            target="custom_target",
            geographic_scope=GeographicScope(type="demo_default"),
            analysis_type="spatial_analysis",
            requires_computer_vision=False,
            confidence=0.9,
            raw_question=question,
        )

    def create_analysis_plan(self, intent, available):
        pass

def test_fallback_accessibility():
    intent = parse_question("Which areas have limited healthcare access?")
    assert intent.intent == "accessibility"
    assert intent.requires_computer_vision is False

def test_fallback_change_detection():
    intent = parse_question("Where has development increased?")
    assert intent.intent == "change_detection"
    assert intent.requires_computer_vision is True

def test_fallback_land_cover():
    intent = parse_question("Show vegetation and forest cover")
    assert intent.intent == "land_cover"
    assert intent.requires_computer_vision is True

def test_fallback_proximity():
    intent = parse_question("Find locations close to the center")
    assert intent.intent == "proximity"
    assert intent.requires_computer_vision is False

def test_fallback_random_text_never_raises():
    intent = parse_question("asdf 1234 !!! random text")
    assert isinstance(intent, QueryIntent)
    assert intent.intent == "accessibility"
    assert intent.confidence == 0.3

def test_fallback_geographic_mentions():
    intent_nairobi = parse_question("Healthcare access in Nairobi")
    assert intent_nairobi.geographic_scope.name == "Nairobi"
    assert intent_nairobi.geographic_scope.type == "named_place"

    intent_kenya = parse_question("Hospital distribution in Kenya")
    assert intent_kenya.geographic_scope.name == "Kenya"
    assert intent_kenya.geographic_scope.type == "named_place"

def test_understand_question_without_ai():
    intent = understand_question("Healthcare in Nairobi", ai=None)
    assert isinstance(intent, QueryIntent)
    assert intent.intent == "accessibility"
    assert intent.geographic_scope.name == "Nairobi"

def test_understand_question_ai_disabled_context():
    ai = DummyAIProvider()
    intent = understand_question("Healthcare in Nairobi", ai=ai, context={"ai_enabled": False})
    assert intent.intent == "accessibility" # Fallback used

def test_understand_question_with_working_ai():
    ai = DummyAIProvider()
    intent = understand_question("Healthcare in Nairobi", ai=ai, context={"ai_enabled": True})
    assert intent.intent == "custom_ai_intent"
    assert intent.confidence == 0.9

def test_understand_question_ai_failure_fallback():
    ai = DummyAIProvider(should_fail=True)
    intent = understand_question("Healthcare in Nairobi", ai=ai)
    assert isinstance(intent, QueryIntent)
    assert intent.intent == "accessibility"

def test_understand_question_ai_invalid_type_fallback():
    ai = DummyAIProvider(return_invalid=True)
    intent = understand_question("Healthcare in Nairobi", ai=ai)
    assert isinstance(intent, QueryIntent)
    assert intent.intent == "accessibility"
