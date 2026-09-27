from app.db.models import Dataset


class DatasetRepository:
    def __init__(self, db):
        self.db = db

    def _to_dict(self, dataset: Dataset) -> dict:
        return {
            "id": dataset.id,
            "name": dataset.name,
            "source": dataset.source,
            "source_url": dataset.source_url,
            "license": dataset.license,
            "coverage": dataset.coverage,
            "resolution": dataset.resolution,
            "crs": dataset.crs,
            "temporal_start": dataset.temporal_start.isoformat() if dataset.temporal_start else None,
            "temporal_end": dataset.temporal_end.isoformat() if dataset.temporal_end else None,
            "update_date": dataset.update_date.isoformat() if dataset.update_date else None,
            "description": dataset.description,
            "limitations": dataset.limitations,
            "imported_at": dataset.imported_at.isoformat() if dataset.imported_at else None,
        }

    def list_all(self) -> list[dict]:
        items = self.db.query(Dataset).all()
        return [self._to_dict(item) for item in items]

    def get_by_name(self, name: str) -> dict | None:
        item = self.db.query(Dataset).filter(Dataset.name == name).first()
        return self._to_dict(item) if item else None

    def create(self, **fields) -> int:
        dataset = Dataset(**fields)
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        return dataset.id
