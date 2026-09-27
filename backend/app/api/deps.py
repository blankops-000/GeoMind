from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db


def db_session() -> Session:
    yield from get_db()


def analysis_repo(db: Session = Depends(db_session)):
    from app.db.repositories.analysis import AnalysisRepository

    return AnalysisRepository(db)


def dataset_repo(db: Session = Depends(db_session)):
    from app.db.repositories.datasets import DatasetRepository

    return DatasetRepository(db)
