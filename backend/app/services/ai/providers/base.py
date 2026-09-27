from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from app.schemas.query import QueryIntent
from app.schemas.plan import AnalysisPlan
from app.schemas.evidence import EvidencePackage

class AIProvider(ABC):
    @abstractmethod
    def understand_query(self, question: str, context: dict[str, Any]) -> QueryIntent:
        """
        Convert user's natural language question into a QueryIntent.
        """
        ...

    @abstractmethod
    def create_analysis_plan(self, intent: QueryIntent, available: dict[str, Any]) -> AnalysisPlan:
        """
        Create a structured AnalysisPlan from QueryIntent and available datasets/capabilities.
        """
        ...

    @abstractmethod
    def interpret_evidence(self, evidence: EvidencePackage) -> dict[str, Any]:
        """
        Interpret structured EvidencePackage into summary and notable insights dict.
        """
        ...

    @abstractmethod
    def generate_insight(self, evidence: EvidencePackage, interpretation: dict[str, Any]) -> dict[str, Any]:
        """
        Generate final user-facing insight dict matching Insight schema fields.
        """
        ...
