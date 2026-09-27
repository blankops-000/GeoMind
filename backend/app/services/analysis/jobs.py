from uuid import UUID
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.analysis.orchestrator import AnalysisOrchestrator


def run_analysis_job(
    analysis_id: UUID | str, question: str, scope: dict | None = None
) -> None:
    """
    Entry point for background execution.
    Opens its own DB session (FastAPI BackgroundTasks
    run after the request session closes).
    """
    db: Session = SessionLocal()
    try:
        orchestrator = AnalysisOrchestrator(db)
        orchestrator.run(analysis_id, question, scope)
    finally:
        db.close()
