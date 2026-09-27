from __future__ import annotations
from typing import Any
from app.services.ai.providers.base import AIProvider
from app.schemas.query import QueryIntent
from app.schemas.plan import AnalysisPlan
from app.schemas.evidence import EvidencePackage

class StubProvider(AIProvider):
    """
    Deterministic, no-network provider.
    Used when AI_ENABLED=false or as a fallback when real AI calls fail.
    """

    def understand_query(self, question: str, context: dict[str, Any]) -> QueryIntent:
        from app.services.query.fallback import parse_question
        return parse_question(question)

    def create_analysis_plan(self, intent: QueryIntent, available: dict[str, Any]) -> AnalysisPlan:
        from app.services.planning.planner import deterministic_template
        datasets = available.get("datasets", []) if isinstance(available, dict) else available
        return deterministic_template(intent, datasets)

    def interpret_evidence(self, evidence: EvidencePackage) -> dict[str, Any]:
        return {
            "summary": (
                f"Analysis of {evidence.area} produced "
                f"{len(evidence.evidence_items)} evidence items."
            ),
            "notable_items": [
                item.description
                for item in evidence.evidence_items[:5]
            ],
        }

    def generate_insight(self, evidence: EvidencePackage, interpretation: dict[str, Any]) -> dict[str, Any]:
        stats = evidence.statistics or {}
        facilities = stats.get("facility_count", 0)
        area = stats.get("region_area_km2", 0.0)
        headline = (
            f"{evidence.area}: {facilities} features across "
            f"{area:.1f} km²"
        )
        key = [item.description for item in evidence.evidence_items[:3]]
        return {
            "headline": headline,
            "summary": interpretation.get("summary", ""),
            "key_findings": key or ["Analysis complete."],
            "confidence": "medium",
        }
