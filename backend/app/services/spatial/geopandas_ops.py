"""Python-side spatial operations using GeoPandas and Shapely."""

from typing import Any, Dict, List, Optional
import numpy as np
import shapely
from shapely.geometry import shape, mapping, box, Polygon, MultiPolygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from app.utils.geometry import simplify_safe, from_geojson_dict, to_geojson_dict


def polygonize_mask(mask_array: np.ndarray, transform: Optional[Any] = None) -> List[Polygon]:
    """Convert a 2D boolean/binary numpy mask array into Shapely Polygons.
    Optionally applies an affine transform.
    """
    if mask_array is None or mask_array.ndim != 2:
        return []

    try:
        import rasterio.features
        polys = []
        for geom_dict, val in rasterio.features.shapes(mask_array.astype(np.uint8), transform=transform):
            if val != 0:
                s_geom = shape(geom_dict)
                if isinstance(s_geom, Polygon):
                    polys.append(s_geom)
                elif isinstance(s_geom, MultiPolygon):
                    polys.extend(s_geom.geoms)
        return polys
    except (ImportError, Exception):
        boxes = []
        rows, cols = mask_array.shape
        for r in range(rows):
            for c in range(cols):
                if mask_array[r, c]:
                    boxes.append(box(c, r, c + 1, r + 1))
        if not boxes:
            return []
        merged = unary_union(boxes)
        if isinstance(merged, Polygon):
            return [merged]
        elif isinstance(merged, MultiPolygon):
            return list(merged.geoms)
        return []


def simplify_features(features: List[Dict[str, Any]], tolerance: float) -> List[Dict[str, Any]]:
    """Simplify geometries in a list of GeoJSON Feature dictionaries."""
    simplified_features = []
    for feat in features:
        feat_copy = dict(feat)
        geom_dict = feat_copy.get("geometry")
        if geom_dict:
            try:
                sh_geom = from_geojson_dict(geom_dict)
                simp_geom = simplify_safe(sh_geom, tolerance)
                feat_copy["geometry"] = to_geojson_dict(simp_geom)
            except Exception:
                pass
        simplified_features.append(feat_copy)
    return simplified_features


def merge_adjacent_polygons(polygons: List[BaseGeometry]) -> BaseGeometry:
    """Merge adjacent or overlapping polygons using Shapely unary_union."""
    if not polygons:
        return Polygon()
    return unary_union(polygons)
