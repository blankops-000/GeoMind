from uuid import UUID
from fastapi import APIRouter, Depends
from app.api.deps import analysis_repo
from app.core.errors import GeoMindError, ErrorCode

router = APIRouter()


@router.get("/{analysis_id}")
def get_analysis(
    analysis_id: UUID,
    repo=Depends(analysis_repo),
):
    run = repo.get_run(analysis_id)
    if not run:
        raise GeoMindError(
            code=ErrorCode.DATASET_NOT_FOUND,
            message="Analysis not found",
            http_status=404,
        )

    status = run["status"]
    status_lower = status.lower() if isinstance(status, str) else ""

    if status_lower == "completed":
        result = repo.get_result(analysis_id)
        if not result:
            raise GeoMindError(
                code=ErrorCode.INTERNAL_ERROR,
                message="Result missing for completed analysis",
                http_status=500,
            )
        return {
            "analysis_id": str(analysis_id),
            "status": "completed",
            "query": run.get("intent") and {
                "original": run["question"],
                "interpreted": run["intent"],
            },
            "map": result.get("geojson") or {
                "type": "FeatureCollection",
                "features": [],
            },
            "statistics": result.get("statistics") or {},
            "findings": result.get("findings") or [],
            "insight": result.get("insight"),
            "provenance": result.get("provenance") or [],
            "confidence": result.get("confidence") or {},
            "limitations": result.get("limitations") or [],
        }

    if status_lower == "failed":
        return {
            "analysis_id": str(analysis_id),
            "status": "failed",
            "error": {
                "code": run.get("error_code") or "ANALYSIS_FAILED",
                "message": run.get("error_message") or "Analysis failed.",
            },
        }

    # processing / any intermediate state
    return {
        "analysis_id": str(analysis_id),
        "status": "processing",
        "progress": run.get("progress", 0),
        "message": run.get("message") or "Processing...",
    }
