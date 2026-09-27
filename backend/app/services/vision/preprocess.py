from __future__ import annotations
from typing import Optional, List, Dict, Tuple, Any
import numpy as np

def validate_imagery(array: Any, expected_bands: Optional[int] = None) -> None:
    """
    Validate imagery shape and data type.
    Raises ValueError on any invalid input.
    """
    if not isinstance(array, np.ndarray):
        raise ValueError("Imagery must be a numpy ndarray")

    if array.size == 0:
        raise ValueError("Imagery array is empty")

    if array.ndim not in (2, 3):
        raise ValueError(f"Imagery must be 2D or 3D, got shape {array.shape}")

    if expected_bands is not None:
        bands = 1 if array.ndim == 2 else min(array.shape[0], array.shape[-1])
        if bands != expected_bands and array.shape[0] != expected_bands and array.shape[-1] != expected_bands:
            raise ValueError(f"Expected {expected_bands} bands, got imagery shape {array.shape}")

def normalize(array: np.ndarray) -> np.ndarray:
    """
    Scale array values to 0.0 .. 1.0 (float32) using min-max normalization.
    """
    if not isinstance(array, np.ndarray):
        raise ValueError("Input must be a numpy ndarray")

    arr_float = array.astype(np.float32)
    min_val = np.min(arr_float)
    max_val = np.max(arr_float)

    if max_val == min_val:
        return np.zeros_like(arr_float)

    return (arr_float - min_val) / (max_val - min_val)

def tile(image: np.ndarray, tile_size: int) -> List[Dict[str, Any]]:
    """
    Non-overlapping tiling of 2D or 3D imagery.
    Returns list of {"data": tile_array, "offset": (row_offset, col_offset)}.
    """
    validate_imagery(image)
    if tile_size <= 0:
        raise ValueError("tile_size must be greater than 0")

    if image.ndim == 2:
        height, width = image.shape
    else:
        # Assuming (C, H, W) or (H, W, C)
        if image.shape[0] < image.shape[1] and image.shape[0] < image.shape[2]:
            _, height, width = image.shape
        else:
            height, width, _ = image.shape

    tiles = []
    for r in range(0, height, tile_size):
        for c in range(0, width, tile_size):
            if image.ndim == 2:
                tile_data = image[r:r+tile_size, c:c+tile_size]
            elif image.shape[0] < image.shape[1] and image.shape[0] < image.shape[2]:
                tile_data = image[:, r:r+tile_size, c:c+tile_size]
            else:
                tile_data = image[r:r+tile_size, c:c+tile_size, :]
            
            tiles.append({
                "data": tile_data,
                "offset": (r, c)
            })
    return tiles

def apply_cloud_mask(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Apply cloud mask (1 = cloud, 0 = clear).
    Sets imagery pixels to 0 where mask is 1.
    """
    validate_imagery(image)
    if not isinstance(mask, np.ndarray):
        raise ValueError("Mask must be a numpy ndarray")

    out = image.copy()
    cloud_bool = (mask > 0)

    if image.ndim == 2:
        out[cloud_bool] = 0
    elif image.shape[0] < image.shape[1] and image.shape[0] < image.shape[2]:
        out[:, cloud_bool] = 0
    else:
        out[cloud_bool, :] = 0

    return out
