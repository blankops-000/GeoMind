import uuid
from datetime import datetime, timezone
from app.db.models import AnalysisRun, AnalysisResult


class AnalysisRepository:
    def __init__(self, db):
        self.db = db

    def _to_uuid(self, val):
        if isinstance(val, str):
            return uuid.UUID(val)
        return val

    def _run_to_dict(self, run: AnalysisRun) -> dict:
        return {
            "id": str(run.id),
            "question": run.question,
            "intent": run.intent,
            "plan": run.plan,
            "status": run.status,
            "progress": run.progress,
            "message": run.message,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "error_code": run.error_code,
            "error_message": run.error_message,
        }

    def _result_to_dict(self, res: AnalysisResult) -> dict:
        return {
            "id": res.id,
            "analysis_id": str(res.analysis_id),
            "geojson": res.geojson,
            "statistics": res.statistics,
            "findings": res.findings,
            "insight": res.insight,
            "provenance": res.provenance,
            "confidence": res.confidence,
            "limitations": res.limitations,
            "created_at": res.created_at.isoformat() if res.created_at else None,
        }

    def create_run(self, analysis_id, question: str) -> None:
        uid = self._to_uuid(analysis_id)
        run = AnalysisRun(id=uid, question=question, status="PENDING", progress=0)
        self.db.add(run)
        self.db.commit()

    def update_status(self, analysis_id, status: str, progress: int, message: str | None = None) -> None:
        uid = self._to_uuid(analysis_id)
        run = self.db.query(AnalysisRun).filter(AnalysisRun.id == uid).first()
        if run:
            run.status = status
            run.progress = progress
            if message is not None:
                run.message = message
            self.db.commit()

    def set_intent(self, analysis_id, intent: dict) -> None:
        uid = self._to_uuid(analysis_id)
        run = self.db.query(AnalysisRun).filter(AnalysisRun.id == uid).first()
        if run:
            run.intent = intent
            self.db.commit()

    def set_plan(self, analysis_id, plan: dict) -> None:
        uid = self._to_uuid(analysis_id)
        run = self.db.query(AnalysisRun).filter(AnalysisRun.id == uid).first()
        if run:
            run.plan = plan
            self.db.commit()

    def mark_completed(self, analysis_id) -> None:
        uid = self._to_uuid(analysis_id)
        run = self.db.query(AnalysisRun).filter(AnalysisRun.id == uid).first()
        if run:
            run.status = "COMPLETED"
            run.progress = 100
            run.completed_at = datetime.now(timezone.utc)
            self.db.commit()

    def mark_failed(self, analysis_id, code: str, message: str) -> None:
        uid = self._to_uuid(analysis_id)
        run = self.db.query(AnalysisRun).filter(AnalysisRun.id == uid).first()
        if run:
            run.status = "FAILED"
            run.error_code = code
            run.error_message = message
            run.completed_at = datetime.now(timezone.utc)
            self.db.commit()

    def get_run(self, analysis_id) -> dict | None:
        uid = self._to_uuid(analysis_id)
        run = self.db.query(AnalysisRun).filter(AnalysisRun.id == uid).first()
        return self._run_to_dict(run) if run else None

    def save_result(self, analysis_id, **payload) -> None:
        uid = self._to_uuid(analysis_id)
        result = AnalysisResult(analysis_id=uid, **payload)
        self.db.add(result)
        self.db.commit()

    def get_result(self, analysis_id) -> dict | None:
        uid = self._to_uuid(analysis_id)
        res = self.db.query(AnalysisResult).filter(AnalysisResult.analysis_id == uid).first()
        return self._result_to_dict(res) if res else None
