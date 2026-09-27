from __future__ import annotations
from app.schemas.vision import VisionInput, VisionResult

class ObjectDetectionProcessor:
    name = "detection"
    version = "0.1.0"

    def process(self, input: VisionInput, task: str, params: dict) -> VisionResult:
        raise NotImplementedError("ObjectDetectionProcessor is not implemented in MVP.")
