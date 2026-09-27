from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict
from app.schemas.vision import VisionInput, VisionResult

class VisionProcessor(ABC):
    name: str = "abstract"
    version: str = "0.0.0"

    @abstractmethod
    def process(
        self,
        input: VisionInput,
        task: str,
        params: dict
    ) -> VisionResult:
        ...

from app.services.vision.classification import ClassificationProcessor
from app.services.vision.detection import ObjectDetectionProcessor
from app.services.vision.segmentation import SegmentationProcessor
from app.services.vision.change_detection import ChangeDetectionProcessor

PROCESSOR_REGISTRY: Dict[str, VisionProcessor] = {
    "classification": ClassificationProcessor(),  # type: ignore
    "segmentation": SegmentationProcessor(),      # type: ignore
    "detection": ObjectDetectionProcessor(),        # type: ignore
    "change_detection": ChangeDetectionProcessor(),# type: ignore
}

def get_processor(task: str) -> VisionProcessor:
    """
    Look up processor instance by task name.
    Raises ValueError if task is unknown.
    """
    if task not in PROCESSOR_REGISTRY:
        raise ValueError(f"Unknown task: {task}")
    return PROCESSOR_REGISTRY[task]
