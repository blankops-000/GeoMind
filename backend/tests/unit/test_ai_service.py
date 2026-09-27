import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.schemas.query import QueryIntent, GeographicScope
from app.schemas.plan import AnalysisPlan
from app.schemas.evidence import EvidencePackage, EvidenceItem
from app.services.ai.service import AIService
from app.services.ai.providers.stub import StubProvider
from app.services.ai.providers.base import AIProvider
from app.services.ai.providers.openai_compatible import OpenAICompatibleProvider, AIServiceError

class BrokenProvider(AIProvider):
    def understand_query(self, question: str, context: dict):
        raise RuntimeError("Provider connection failed")

    def create_analysis_plan(self, intent: QueryIntent, available: dict):
        raise RuntimeError("Provider connection failed")

    def interpret_evidence(self, evidence: EvidencePackage):
        raise RuntimeError("Provider connection failed")

    def generate_insight(self, evidence: EvidencePackage, interpretation: dict):
        raise RuntimeError("Provider connection failed")

@pytest.fixture
def sample_evidence_package():
    return EvidencePackage(
        analysis_id=uuid4(),
        area="Nairobi",
        datasets=["facilities", "geographic_regions"],
        evidence_items=[
            EvidenceItem(
                evidence_type="spatial",
                description="facilities count = 12",
                value=12,
                source="PostGIS",
                confidence=0.9,
            )
        ],
        statistics={"facility_count": 12, "region_area_km2": 45.5},
        confidence={"overall": 0.9},
        provenance=[],
        limitations=["Confidence reflects model output, not analytical truth"],
    )

def test_ai_service_stub_understand_query():
    service = AIService(provider=StubProvider())
    intent = service.understand_query("What healthcare facilities exist in Nairobi?")
    assert isinstance(intent, QueryIntent)
    assert intent.geographic_scope.name == "Nairobi"
    assert intent.raw_question == "What healthcare facilities exist in Nairobi?"

def test_ai_service_fallback_on_broken_provider():
    service = AIService(provider=BrokenProvider())
    
    # All methods should fall back to StubProvider gracefully without raising
    intent = service.understand_query("Healthcare facilities in Nairobi")
    assert isinstance(intent, QueryIntent)
    assert intent.geographic_scope.name == "Nairobi"

    plan = service.create_analysis_plan(intent, {"datasets": ["facilities", "geographic_regions"]})
    assert isinstance(plan, AnalysisPlan)
    assert "facilities" in plan.datasets

def test_ai_service_interpret_evidence(sample_evidence_package):
    service = AIService(provider=StubProvider())
    interp = service.interpret_evidence(sample_evidence_package)
    assert isinstance(interp, dict)
    assert "summary" in interp
    assert "notable_items" in interp
    assert "facilities count = 12" in interp["notable_items"]

def test_ai_service_generate_insight(sample_evidence_package):
    service = AIService(provider=StubProvider())
    interp = service.interpret_evidence(sample_evidence_package)
    insight = service.generate_insight(sample_evidence_package, interp)
    
    assert isinstance(insight, dict)
    assert "headline" in insight
    assert "summary" in insight
    assert "key_findings" in insight
    assert "Nairobi" in insight["headline"]

def test_openai_compatible_provider_mocked():
    provider = OpenAICompatibleProvider(
        base_url="http://mock-ai:8000/v1",
        api_key="sk-test-key",
        model="gpt-4o-mini",
    )
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"summary": "Mocked AI summary", "notable_items": ["item1"]}'
                }
            }
        ]
    }
    mock_response.raise_for_status.return_value = None

    with patch("httpx.Client.post", return_value=mock_response):
        package = EvidencePackage(
            analysis_id=uuid4(),
            area="Test Area",
            evidence_items=[
                EvidenceItem(
                    evidence_type="spatial",
                    description="test item",
                    source="test source",
                )
            ]
        )
        res = provider.interpret_evidence(package)
        assert res["summary"] == "Mocked AI summary"

def test_openai_compatible_provider_raises_error_on_network_failure():
    provider = OpenAICompatibleProvider(
        base_url="http://mock-ai:8000/v1",
        api_key="sk-test-key",
        model="gpt-4o-mini",
        max_retries=0,
    )
    with patch("httpx.Client.post", side_effect=Exception("Connection refused")):
        package = EvidencePackage(
            analysis_id=uuid4(),
            area="Test Area",
            evidence_items=[
                EvidenceItem(
                    evidence_type="spatial",
                    description="test item",
                    source="test source",
                )
            ]
        )
        with pytest.raises(AIServiceError):
            provider.interpret_evidence(package)
