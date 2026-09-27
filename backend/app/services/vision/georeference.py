from __future__ import annotations
from typing import Optional, List, Tuple, Any, Dict
import numpy as np
from pyproj import Transformer
from shapely.geometry import Polygon, mapping, shape
from app.utils.geometry import validate_geometry, repair_geometry

def _apply_affine_transform(coords: List[Tuple[float, float]], affine_transform: Any) -> List[Tuple[float, float]]:
    """
    Transform pixel (x, y) coordinates to source CRS coordinates using affine_transform.
    Supports rasterio.Affine, objects with __mul__, or (a, b, c, d, e, f) tuples.
    """
    if isinstance(affine_transform, (tuple, list)) and len(affine_transform) == 6:
        a, b, c, d, e, f = affine_transform
        return [(a * x + b * y + c, d * x + e * y + f) for (x, y) in coords]
    
    if hasattr(affine_transform, "__mul__"):
        try:
            return [affine_transform * (x, y) for (x, y) in coords]
        except Exception:
            pass

    if hasattr(affine_transform, "c"):
        # rasterio Affine style object
        a = getattr(affine_transform, "a", 1.0)
        b = getattr(affine_transform, "b", 0.0)
        c = getattr(affine_transform, "c", 0.0)
        d = getattr(affine_transform, "d", 0.0)
        e = getattr(affine_transform, "e", 1.0)
        f = getattr(affine_transform, "f", 0.0)
        return [(a * x + b * y + c, d * x + e * y + f) for (x, y) in coords]

    raise ValueError(f"Unsupported affine transform format: {type(affine_transform)}")

def pixel_to_geographic(
    pixel_polygon: Polygon,
    affine_transform: Any,
    src_crs: str,
    dst_crs: str = "EPSG:4326",
) -> Optional[dict]:
    """
    1. Apply affine transform: pixel -> source CRS
    2. Transform source CRS -> dst_crs via PyProj
    3. Build Shapely geometry
    4. Validate / repair
    5. Return GeoJSON dict or None if invalid
    """
    if affine_transform is None or src_crs is None:
        raise ValueError("Missing affine or CRS")

    if pixel_polygon is None or pixel_polygon.is_empty:
        return None

    # Step 1: Pixel -> Source CRS
    pixel_coords = list(pixel_polygon.exterior.coords)
    src_coords = _apply_affine_transform(pixel_coords, affine_transform)

    # Step 2: Source CRS -> Target CRS
    transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    dst_coords = [transformer.transform(x, y) for (x, y) in src_coords]

    # Step 3: Build Shapely Polygon
    geom = Polygon(dst_coords)

    # Step 4: Validate and repair if needed
    if not validate_geometry(geom):
        geom = repair_geometry(geom)

    if not validate_geometry(geom):
        return None

    return mapping(geom)

def bbox_to_geographic(
    bbox_pixel: Tuple[float, float, float, float],
    affine_transform: Any,
    src_crs: str,
    dst_crs: str = "EPSG:4326",
) -> Optional[dict]:
    """
    Convenience: convert a pixel bbox (minx, miny, maxx, maxy)
    into a georeferenced GeoJSON Polygon.
    """
    minx, miny, maxx, maxy = bbox_pixel
    pixel_polygon = Polygon([(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy), (minx, miny)])
    return pixel_to_geographic(pixel_polygon, affine_transform, src_crs, dst_crs)

def mask_to_polygons(
    mask: np.ndarray,
    affine_transform: Any,
    src_crs: str,
    dst_crs: str = "EPSG:4326",
) -> List[dict]:
    """
    Convert boolean/binary mask -> list of georeferenced GeoJSON polygons.
    Uses rasterio.features.shapes if available, else a scipy.ndimage.label fallback.
    """
    if mask is None or not np.any(mask):
        return []

    try:
        import rasterio.features
        # rasterio features shapes return pixel or world shapes depending on transform passed
        polygons = []
        shapes = rasterio.features.shapes(
            mask.astype(np.uint8),
            mask=(mask > 0),
            transform=affine_transform
        )
        transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)

        for geom_dict, val in shapes:
            poly = shape(geom_dict)
            if poly.is_empty:
                continue
            # Transform poly coords from src_crs to dst_crs
            transformed_coords = [
                transformer.transform(x, y) for (x, y) in poly.exterior.coords
            ]
            dst_poly = Polygon(transformed_coords)
            if not validate_geometry(dst_poly):
                dst_poly = repair_geometry(dst_poly)
            if validate_geometry(dst_poly):
                polygons.append(mapping(dst_poly))
        return polygons

    except ImportError:
        # Fallback using scipy.ndimage.label
        from scipy.ndimage import label, find_objects

        labeled, num_features = label(mask > 0)
        slices = find_objects(labeled)
        polygons = []

        for idx, slc in enumerate(slices, start=1):
            if slc is None:
                continue
            row_slice, col_slice = slc
            miny, maxy = row_slice.start, row_slice.stop
            minx, maxx = col_slice.start, col_slice.stop

            bbox_poly = bbox_to_geographic(
                (float(minx), float(miny), float(maxx), float(maxy)),
                affine_transform,
                src_crs,
                dst_crs
            )
            if bbox_poly is not None:
                polygons.append(bbox_poly)

        return polygons
