from __future__ import annotations
import logging
from typing import Optional, Any

from app.schemas.query import QueryIntent
from app.schemas.plan import AnalysisPlan
from app.schemas.evidence import EvidencePackage
from app.services.ai.providers.base import AIProvider
from app.services.ai.providers.stub import StubProvider
from app.services.ai.providers.openai_compatible import OpenAICompatibleProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIService:
    """
    Main AI Service managing provider execution with fail-safe fallback to StubProvider.
    Ensures GeoMind AI never crashes due to LLM provider downtime or format errors.
    """

    def __init__(self, provider: Optional[AIProvider] = None):
        if provider is None:
            provider = self._build_default_provider()
        self.provider = provider
        self.stub = StubProvider()

    def understand_query(
        self, question: str, context: Optional[dict[str, Any]] = None
    ) -> QueryIntent:
        try:
            return self.provider.understand_query(question, context or {})
        except Exception as exc:
            logger.warning(
                f"AIService understand_query failed with provider {type(self.provider).__name__}: {exc}. "
                "Falling back to StubProvider."
            )
            return self.stub.understand_query(question, context or {})

    def create_analysis_plan(
        self, intent: QueryIntent, available: dict[str, Any]
    ) -> AnalysisPlan:
        try:
            return self.provider.create_analysis_plan(intent, available)
        except Exception as exc:
            logger.warning(
                f"AIService create_analysis_plan failed with provider {type(self.provider).__name__}: {exc}. "
                "Falling back to StubProvider."
            )
            return self.stub.create_analysis_plan(intent, available)

    def interpret_evidence(self, evidence: EvidencePackage) -> dict[str, Any]:
        try:
            return self.provider.interpret_evidence(evidence)
        except Exception as exc:
            logger.warning(
                f"AIService interpret_evidence failed with provider {type(self.provider).__name__}: {exc}. "
                "Falling back to StubProvider."
            )
            return self.stub.interpret_evidence(evidence)

    def generate_insight(
        self, evidence: EvidencePackage, interpretation: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            return self.provider.generate_insight(evidence, interpretation)
        except Exception as exc:
            logger.warning(
                f"AIService generate_insight failed with provider {type(self.provider).__name__}: {exc}. "
                "Falling back to StubProvider."
            )
            return self.stub.generate_insight(evidence, interpretation)

    def _build_default_provider(self) -> AIProvider:
        if not getattr(settings, "AI_ENABLED", True) or getattr(settings, "AI_PROVIDER", "stub") == "stub":
            return StubProvider()
        try:
            return OpenAICompatibleProvider(
                base_url=getattr(settings, "AI_BASE_URL", "https://api.openai.com/v1"),
                api_key=getattr(settings, "AI_API_KEY", None),
                model=getattr(settings, "AI_MODEL", "gpt-4o-mini"),
                timeout=getattr(settings, "AI_TIMEOUT_SECONDS", 20),
                max_retries=getattr(settings, "AI_MAX_RETRIES", 2),
            )
        except Exception as exc:
            logger.warning(
                f"Failed to initialize OpenAICompatibleProvider: {exc}. Falling back to StubProvider."
            )
            return StubProvider()
