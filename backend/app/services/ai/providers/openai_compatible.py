from __future__ import annotations
import json
import logging
from typing import Any, Optional
import httpx

from app.schemas.query import QueryIntent
from app.schemas.plan import AnalysisPlan
from app.schemas.evidence import EvidencePackage
from app.schemas.result import Insight
from app.core.errors import GeoMindError, ErrorCode
from app.services.ai.providers.base import AIProvider
from app.services.ai.prompts import (
    UNDERSTAND_QUERY_PROMPT,
    CREATE_PLAN_PROMPT,
    INTERPRET_EVIDENCE_PROMPT,
    GENERATE_INSIGHT_PROMPT,
)

logger = logging.getLogger(__name__)

class AIServiceError(GeoMindError):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.AI_SERVICE_FAILED,
            message=message,
            http_status=503,
            details=details or {},
        )

def _clean_json_text(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

class OpenAICompatibleProvider(AIProvider):
    """
    OpenAI-compatible API provider for LLM integrations.
    Sends network requests to base_url/chat/completions and parses JSON outputs.
    """

    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        timeout: int = 20,
        max_retries: int = 2,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    def _call_api(self, prompt: str) -> str:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
        }

        last_exception: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return content
            except Exception as exc:
                last_exception = exc
                logger.warning(
                    f"OpenAI API call attempt {attempt + 1}/{self.max_retries + 1} failed: {exc}"
                )

        raise AIServiceError(
            message=f"OpenAI compatible API request failed after {self.max_retries + 1} attempts: {last_exception}",
            details={"model": self.model, "error": str(last_exception)},
        )

    def understand_query(self, question: str, context: dict[str, Any]) -> QueryIntent:
        try:
            prompt = UNDERSTAND_QUERY_PROMPT.format(
                schema=json.dumps(QueryIntent.model_json_schema()),
                question=question,
                context=json.dumps(context or {}),
            )
            raw = self._call_api(prompt)
            cleaned = _clean_json_text(raw)
            return QueryIntent.model_validate_json(cleaned)
        except AIServiceError:
            raise
        except Exception as exc:
            raise AIServiceError(
                message=f"Failed to parse understand_query response: {exc}",
                details={"error": str(exc)},
            ) from exc

    def create_analysis_plan(self, intent: QueryIntent, available: dict[str, Any]) -> AnalysisPlan:
        try:
            prompt = CREATE_PLAN_PROMPT.format(
                schema=json.dumps(AnalysisPlan.model_json_schema()),
                intent_json=intent.model_dump_json(),
                available_json=json.dumps(available or {}),
            )
            raw = self._call_api(prompt)
            cleaned = _clean_json_text(raw)
            return AnalysisPlan.model_validate_json(cleaned)
        except AIServiceError:
            raise
        except Exception as exc:
            raise AIServiceError(
                message=f"Failed to parse create_analysis_plan response: {exc}",
                details={"error": str(exc)},
            ) from exc

    def interpret_evidence(self, evidence: EvidencePackage) -> dict[str, Any]:
        try:
            prompt = INTERPRET_EVIDENCE_PROMPT.format(
                evidence_json=evidence.model_dump_json(),
            )
            raw = self._call_api(prompt)
            cleaned = _clean_json_text(raw)
            data = json.loads(cleaned)
            if not isinstance(data, dict) or "summary" not in data:
                raise ValueError("Response must be a JSON dict containing 'summary'")
            return data
        except AIServiceError:
            raise
        except Exception as exc:
            raise AIServiceError(
                message=f"Failed to interpret evidence: {exc}",
                details={"error": str(exc)},
            ) from exc

    def generate_insight(self, evidence: EvidencePackage, interpretation: dict[str, Any]) -> dict[str, Any]:
        try:
            prompt = GENERATE_INSIGHT_PROMPT.format(
                schema=json.dumps(Insight.model_json_schema()),
                evidence_json=evidence.model_dump_json(),
                interpretation_json=json.dumps(interpretation or {}),
            )
            raw = self._call_api(prompt)
            cleaned = _clean_json_text(raw)
            data = json.loads(cleaned)
            insight = Insight.model_validate(data)
            return insight.model_dump()
        except AIServiceError:
            raise
        except Exception as exc:
            raise AIServiceError(
                message=f"Failed to generate insight: {exc}",
                details={"error": str(exc)},
            ) from exc
