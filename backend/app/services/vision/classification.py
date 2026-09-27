from __future__ import annotations
from app.schemas.vision import VisionInput, VisionResult

class ClassificationProcessor:
    name = "classification"
    version = "0.1.0"

    def process(self, input: VisionInput, task: str, params: dict) -> VisionResult:
        raise NotImplementedError("ClassificationProcessor is not implemented in MVP.")
