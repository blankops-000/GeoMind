from __future__ import annotations
import logging
from typing import Protocol, Optional, Any, Dict
from app.schemas.query import QueryIntent
from app.services.query import fallback

logger = logging.getLogger(__name__)

class AIProvider(Protocol):
    def understand_query(self, question: str, context: dict) -> QueryIntent: ...
    def create_analysis_plan(self, intent: QueryIntent, available: dict) -> Any: ...

def understand_question(
    question: str,
    ai: AIProvider | None = None,
    context: dict | None = None
) -> QueryIntent:
    """
    Try AI understanding. On any failure or timeout,
    fall back to deterministic keyword parser.
    Always returns a valid QueryIntent.
    """
    ctx = context or {}
    if ai is None or ctx.get("ai_enabled") is False:
        return fallback.parse_question(question)

    try:
        intent = ai.understand_query(question, ctx)
        if not isinstance(intent, QueryIntent):
            raise ValueError(f"AI returned invalid type: {type(intent)}")
        return intent
    except Exception as exc:
        logger.warning(f"AI query understanding failed, using fallback: {exc}")
        return fallback.parse_question(question)
