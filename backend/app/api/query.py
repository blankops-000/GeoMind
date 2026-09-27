from uuid import uuid4
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field, field_validator
from app.api.deps import analysis_repo

router = APIRouter()


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    location: Optional[dict] = None

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: Optional[dict]) -> Optional[dict]:
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("Location must be a dictionary")
        if "type" not in v:
            raise ValueError("GeoJSON location must have a 'type' field")
        return v


class QueryResponse(BaseModel):
    analysis_id: str
    status: str
    message: str


@router.post("", response_model=QueryResponse, status_code=202)
def submit_query(
    req: QueryRequest,
    background: BackgroundTasks,
    repo=Depends(analysis_repo),
):
    analysis_id = uuid4()

    # Register run in DB immediately
    repo.create_run(analysis_id, req.question)

    # Schedule background execution
    from app.services.analysis.jobs import run_analysis_job

    background.add_task(
        run_analysis_job,
        analysis_id,
        req.question,
        req.location,
    )

    return QueryResponse(
        analysis_id=str(analysis_id),
        status="processing",
        message="Analysis started",
    )
