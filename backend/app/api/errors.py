from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.errors import GeoMindError, ErrorCode
from app.core.logging import get_logger

logger = get_logger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(GeoMindError)
    async def geomind_error_handler(request: Request, exc: GeoMindError):
        logger.error(f"GeoMindError: {exc.code} - {exc.message}")
        code_val = exc.code.value if hasattr(exc.code, "value") else str(exc.code)
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "error": {
                    "code": code_val,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred.",
                }
            },
        )
