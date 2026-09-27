import pytest
import numpy as np
from shapely.geometry import shape
from app.schemas.vision import VisionInput, VisionResult
from app.services.vision.processor import get_processor, PROCESSOR_REGISTRY
from app.services.vision.segmentation import SegmentationProcessor
from app.services.vision.change_detection import ChangeDetectionProcessor
from app.services.vision.preprocess import (
    validate_imagery,
    normalize,
    tile,
    apply_cloud_mask,
)
from app.utils.geometry import validate_geometry

def test_get_processor_registry():
    seg_proc = get_processor("segmentation")
    assert isinstance(seg_proc, SegmentationProcessor)

    change_proc = get_processor("change_detection")
    assert isinstance(change_proc, ChangeDetectionProcessor)

def test_processor_stubs_raise_not_implemented():
    class_proc = get_processor("classification")
    det_proc = get_processor("detection")

    v_input = VisionInput(imagery_ref="mock_sat.tif", task="classification")
    
    with pytest.raises(NotImplementedError):
        class_proc.process(v_input, "classification", {})

    with pytest.raises(NotImplementedError):
        det_proc.process(v_input, "detection", {})

def test_get_processor_unknown_raises():
    with pytest.raises(ValueError):
        get_processor("mars_rover_vision")

def test_segmentation_processor_active_end_to_end():
    proc = get_processor("segmentation")
    v_input = VisionInput(
        imagery_ref="sentinel2_nairobi.tif",
        task="segmentation",
        parameters={"target_feature": "vegetation"}
    )

    result = proc.process(v_input, "segmentation", {})
    assert isinstance(result, VisionResult)
    assert result.task_type == "segmentation"
    assert result.regions is not None
    assert len(result.regions) > 0
    assert result.area_km2 is not None and result.area_km2 > 0

    for r in result.regions:
        geom = shape(r)
        assert validate_geometry(geom)

def test_change_detection_processor_active_end_to_end():
    proc = get_processor("change_detection")
    v_input = VisionInput(
        imagery_ref="sentinel2_change.tif",
        task="change_detection",
        parameters={"target_feature": "built_up"}
    )

    result = proc.process(v_input, "change_detection", {})
    assert isinstance(result, VisionResult)
    assert result.task_type == "change_detection"
    assert result.regions is not None
    assert len(result.regions) > 0
    assert result.area_km2 is not None and result.area_km2 > 0
    assert "change_percent" in result.statistics

def test_preprocess_validate_imagery():
    valid_arr = np.ones((100, 100, 3), dtype=np.uint8)
    validate_imagery(valid_arr, expected_bands=3)

    with pytest.raises(ValueError):
        validate_imagery("not_an_array")

    with pytest.raises(ValueError):
        validate_imagery(np.ones((100, 100, 3)), expected_bands=5)

def test_preprocess_normalize():
    arr = np.array([[10, 20], [30, 40]], dtype=np.float32)
    norm = normalize(arr)
    assert norm.min() == 0.0
    assert norm.max() == 1.0

def test_preprocess_tile():
    arr = np.ones((100, 100), dtype=np.uint8)
    tiles = tile(arr, tile_size=50)
    assert len(tiles) == 4
    assert tiles[0]["data"].shape == (50, 50)

def test_preprocess_apply_cloud_mask():
    arr = np.ones((10, 10), dtype=np.uint8) * 100
    cloud_mask = np.zeros((10, 10), dtype=np.uint8)
    cloud_mask[0:5, 0:5] = 1

    masked = apply_cloud_mask(arr, cloud_mask)
    assert (masked[0:5, 0:5] == 0).all()
    assert (masked[5:10, 5:10] == 100).all()
