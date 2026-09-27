from enum import Enum
from typing import Optional, Dict, Any

class ErrorCode(str, Enum):
    INVALID_QUERY = "INVALID_QUERY"
    INVALID_GEOMETRY = "INVALID_GEOMETRY"
    UNSUPPORTED_ANALYSIS = "UNSUPPORTED_ANALYSIS"
    DATASET_NOT_FOUND = "DATASET_NOT_FOUND"
    NO_DATA = "NO_DATA"
    SPATIAL_ANALYSIS_FAILED = "SPATIAL_ANALYSIS_FAILED"
    CV_PROCESSING_FAILED = "CV_PROCESSING_FAILED"
    AI_SERVICE_FAILED = "AI_SERVICE_FAILED"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"

ERROR_STATUS_MAP: Dict[ErrorCode, int] = {
    ErrorCode.INVALID_QUERY: 400,
    ErrorCode.INVALID_GEOMETRY: 400,
    ErrorCode.UNSUPPORTED_ANALYSIS: 422,
    ErrorCode.DATASET_NOT_FOUND: 404,
    ErrorCode.NO_DATA: 404,
    ErrorCode.SPATIAL_ANALYSIS_FAILED: 500,
    ErrorCode.CV_PROCESSING_FAILED: 500,
    ErrorCode.AI_SERVICE_FAILED: 503,
    ErrorCode.ANALYSIS_FAILED: 500,
    ErrorCode.INTERNAL_ERROR: 500,
}

class GeoMindError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        http_status: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.http_status = http_status or ERROR_STATUS_MAP.get(code, 500)
        self.details = details or {}
        super().__init__(self.message)
