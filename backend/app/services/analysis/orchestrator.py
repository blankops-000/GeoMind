from __future__ import annotations

import logging
from enum import Enum
from typing import Protocol, Optional, Any
from uuid import UUID

from app.core.constants import PROGRESS_MAP
from app.core.errors import GeoMindError, ErrorCode
from app.db.repositories.analysis import AnalysisRepository
from app.schemas.evidence import EvidencePackage
from app.schemas.plan import AnalysisPlan
from app.schemas.query import QueryIntent
from app.schemas.result import AnalysisResult, Finding, Insight
from app.schemas.vision import VisionInput, VisionResult
from app.services.analysis.state import AnalysisState

logger = logging.getLogger(__name__)


class SpatialEngineProtocol(Protocol):
    def execute(self, plan: AnalysisPlan) -> object: ...


class VisionProcessorProtocol(Protocol):
    def process(
        self, input: VisionInput, task: str, params: dict
    ) -> VisionResult: ...


class AIServiceProtocol(Protocol):
    def understand_query(
        self, question: str, context: dict
    ) -> QueryIntent: ...

    def create_analysis_plan(
        self, intent: QueryIntent, available: dict
    ) -> AnalysisPlan: ...

    def interpret_evidence(
        self, evidence: EvidencePackage
    ) -> dict: ...

    def generate_insight(
        self, evidence: EvidencePackage, interpretation: dict
    ) -> dict: ...


class EvidenceBuilderProtocol(Protocol):
    def build(self, **kwargs) -> EvidencePackage: ...


class AnalysisOrchestrator:
    def __init__(self, db: Any, ai_service: AIServiceProtocol | None = None):
        self.db = db
        self.repo = AnalysisRepository(db)
        self.ai = ai_service  # may be None -> lazy init

    def run(
        self,
        analysis_id: UUID | str,
        question: str,
        scope: dict | None = None,
    ) -> AnalysisResult:
        """
        Execute the full pipeline.
        Persist progress at each stage.
        On failure, mark analysis as FAILED and raise.
        """
        try:
            return self._execute_pipeline(analysis_id, question, scope)
        except GeoMindError as e:
            logger.error(
                f"Analysis {analysis_id} failed with GeoMindError: {e.message}",
                exc_info=True,
            )
            code_str = e.code.value if hasattr(e.code, "value") else str(e.code)
            self.repo.mark_failed(analysis_id, code_str, e.message)
            raise
        except Exception as e:
            logger.error(
                f"Analysis {analysis_id} failed with unhandled exception: {str(e)}",
                exc_info=True,
            )
            code_str = ErrorCode.ANALYSIS_FAILED.value
            err_msg = str(e) or "Analysis pipeline failed"
            self.repo.mark_failed(analysis_id, code_str, err_msg)
            raise GeoMindError(code=ErrorCode.ANALYSIS_FAILED, message=err_msg) from e

    def _execute_pipeline(
        self,
        analysis_id: UUID | str,
        question: str,
        scope: dict | None = None,
    ) -> AnalysisResult:
        # Step 1: Create run
        self.repo.create_run(analysis_id, question)
        self._set_state(analysis_id, AnalysisState.CREATED)

        # Step 2: Query Understanding
        self._set_state(analysis_id, AnalysisState.UNDERSTANDING)
        from app.services.query.understanding import understand_question

        context = {"scope": scope} if scope else {}
        intent = understand_question(question, self._get_ai(), context=context)
        intent_dict = (
            intent.model_dump() if hasattr(intent, "model_dump") else intent.dict()
        )
        self.repo.set_intent(analysis_id, intent_dict)

        # Step 3: Analysis Planning
        self._set_state(analysis_id, AnalysisState.PLANNING)
        from app.services.planning.planner import plan_analysis

        available = self._list_available_datasets()
        plan = plan_analysis(intent, self._get_ai(), available)

        # Step 4: Plan Validation
        from app.services.planning.validator import validate_plan

        plan = validate_plan(plan, available)
        plan_dict = (
            plan.model_dump() if hasattr(plan, "model_dump") else plan.dict()
        )
        self.repo.set_plan(analysis_id, plan_dict)
        self._set_state(analysis_id, AnalysisState.PLAN_VALIDATED)

        # Step 5: Data Retrieval
        self._set_state(analysis_id, AnalysisState.DATA_RETRIEVAL)
        # (for MVP: PostGIS already loaded)

        # Step 6: Spatial Analysis
        self._set_state(analysis_id, AnalysisState.SPATIAL_ANALYSIS)
        from app.services.spatial.engine import SpatialEngine

        spatial_engine = SpatialEngine(self.db)
        spatial_result = spatial_engine.execute(plan)

        # Step 7: Computer Vision
        vision_results = []
        if plan.cv_operations:
            self._set_state(analysis_id, AnalysisState.COMPUTER_VISION)
            from app.services.vision.processor import get_processor

            scope_dict = (
                plan.geographic_scope.model_dump()
                if hasattr(plan.geographic_scope, "model_dump")
                else plan.geographic_scope.dict()
            )
            for cv_op in plan.cv_operations:
                processor = get_processor(cv_op.task)
                vin = VisionInput(
                    imagery_ref=cv_op.imagery_source,
                    task=cv_op.task,
                    parameters={},
                    geographic_scope=scope_dict,
                )
                try:
                    vr = processor.process(vin, cv_op.task, {})
                    vr.analysis_id = analysis_id
                    vr_dict = (
                        vr.model_dump()
                        if hasattr(vr, "model_dump")
                        else vr.dict()
                    )
                    vision_results.append(vr_dict)
                except NotImplementedError:
                    # stub processor; skip gracefully
                    pass

        # Step 8: Evidence Building
        self._set_state(analysis_id, AnalysisState.EVIDENCE_BUILDING)
        from app.services.evidence.builder import build_evidence_package
        from app.services.evidence.validator import EvidenceValidator

        area_name = getattr(plan.geographic_scope, "name", None) or "Selected area"
        spatial_res_dict = (
            spatial_result.__dict__
            if hasattr(spatial_result, "__dict__")
            else (spatial_result if isinstance(spatial_result, dict) else {})
        )
        stats_dict = getattr(spatial_result, "statistics", {})
        prov_list = getattr(spatial_result, "provenance", [])

        evidence = build_evidence_package(
            analysis_id=analysis_id,
            area=area_name,
            datasets=plan.datasets,
            spatial_result=spatial_res_dict,
            vision_results=vision_results,
            statistics=stats_dict,
            provenance=prov_list,
        )
        EvidenceValidator().validate(evidence)

        # Step 9: AI Reasoning
        self._set_state(analysis_id, AnalysisState.AI_REASONING)
        ai = self._get_ai()
        interpretation = ai.interpret_evidence(evidence)
        insight_dict = ai.generate_insight(evidence, interpretation)

        insight = Insight(**insight_dict)

        # Step 10: Result Validation
        self._set_state(analysis_id, AnalysisState.VALIDATION)
        result = AnalysisResult(
            analysis_id=analysis_id,
            status="completed",
            query={
                "original": question,
                "interpreted": intent_dict,
            },
            map={
                "type": "FeatureCollection",
                "features": evidence.geographic_features,
            },
            statistics=evidence.statistics,
            findings=[
                Finding(
                    title=item.description[:80],
                    description=item.description,
                    confidence=item.confidence,
                )
                for item in evidence.evidence_items[:10]
            ],
            insight=insight,
            provenance=evidence.provenance,
            confidence=evidence.confidence,
            limitations=evidence.limitations,
        )

        # Step 11: Completion & Persistence
        res_dict = (
            result.model_dump()
            if hasattr(result, "model_dump")
            else result.dict()
        )
        insight_data = (
            result.insight.model_dump()
            if hasattr(result.insight, "model_dump")
            else result.insight.dict()
        )
        save_payload = {
            "geojson": res_dict.get("map"),
            "statistics": res_dict.get("statistics"),
            "findings": [
                f.model_dump() if hasattr(f, "model_dump") else f.dict()
                for f in result.findings
            ],
            "insight": insight_data,
            "provenance": res_dict.get("provenance"),
            "confidence": res_dict.get("confidence"),
            "limitations": res_dict.get("limitations"),
        }
        self.repo.save_result(analysis_id, **save_payload)
        self.repo.mark_completed(analysis_id)
        return result

    def _set_state(
        self,
        analysis_id: UUID | str,
        state: AnalysisState,
        message: str | None = None,
    ) -> None:
        state_str = state.value if isinstance(state, Enum) else str(state)
        progress = PROGRESS_MAP.get(state_str, 0)
        self.repo.update_status(analysis_id, state_str, progress, message)

    def _get_ai(self) -> AIServiceProtocol:
        if self.ai is None:
            from app.services.ai.service import AIService

            self.ai = AIService()
        return self.ai

    def _list_available_datasets(self) -> list[str]:
        from app.db.repositories.datasets import DatasetRepository

        repo = DatasetRepository(self.db)
        rows = repo.list_all()
        return [r["name"] for r in rows]
