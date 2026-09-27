from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.deps import db_session
from app.core.config import settings

router = APIRouter()


@router.get("")
@router.get("/")
def health(db: Session = Depends(db_session)):
    db_status = "unavailable"
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        pass

    ai_status = "disabled" if not settings.AI_ENABLED else "ok"

    return {
        "status": "ok",
        "database": db_status,
        "ai": ai_status,
        "version": "0.1.0",
    }
