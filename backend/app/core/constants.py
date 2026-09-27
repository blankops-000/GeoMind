from app.core.config import settings

DEFAULT_SRID = 4326
DEMO_UTM_EPSG = settings.DEMO_UTM_EPSG

ANALYSIS_STATES = [
    "created",
    "understanding",
    "planning",
    "plan_validated",
    "data_retrieval",
    "spatial_analysis",
    "computer_vision",
    "evidence_building",
    "ai_reasoning",
    "validation",
    "completed",
    "failed",
]

PROGRESS_MAP = {
    "created": 0,
    "understanding": 10,
    "planning": 20,
    "plan_validated": 25,
    "data_retrieval": 35,
    "spatial_analysis": 55,
    "computer_vision": 70,
    "evidence_building": 80,
    "ai_reasoning": 90,
    "validation": 95,
    "completed": 100,
    "failed": 100,
}

SUPPORTED_SPATIAL_OPS = [
    "intersection",
    "within",
    "dwithin",
    "buffer",
    "area",
    "count",
    "aggregate",
    "distance",
]

SUPPORTED_CV_TASKS = [
    "classification",
    "segmentation",
    "detection",
    "change_detection",
]
