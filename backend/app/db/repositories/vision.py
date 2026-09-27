import uuid
from app.db.models import VisionResult


class VisionRepository:
    def __init__(self, db):
        self.db = db

    def _to_uuid(self, val):
        if val is None:
            return None
        if isinstance(val, str):
            return uuid.UUID(val)
        return val

    def _to_dict(self, res: VisionResult) -> dict:
        return {
            "id": res.id,
            "analysis_id": str(res.analysis_id) if res.analysis_id else None,
            "task_type": res.task_type,
            "model_name": res.model_name,
            "model_version": res.model_version,
            "label": res.label,
            "confidence": float(res.confidence) if res.confidence is not None else None,
            "area_km2": float(res.area_km2) if res.area_km2 is not None else None,
            "metadata": res.metadata_,
            "created_at": res.created_at.isoformat() if res.created_at else None,
        }

    def save(self, analysis_id, **fields) -> int:
        uid = self._to_uuid(analysis_id)
        if "metadata" in fields:
            fields["metadata_"] = fields.pop("metadata")
        result = VisionResult(analysis_id=uid, **fields)
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result.id

    def list_by_analysis(self, analysis_id) -> list[dict]:
        uid = self._to_uuid(analysis_id)
        items = self.db.query(VisionResult).filter(VisionResult.analysis_id == uid).all()
        return [self._to_dict(item) for item in items]
