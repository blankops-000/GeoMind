"""Geometry validation, repair, simplification, and GeoJSON conversion utilities."""

from typing import Any, Dict, Optional
import shapely
from shapely.geometry import shape, mapping
from shapely.geometry.base import BaseGeometry


def validate_geometry(geom: Optional[BaseGeometry]) -> bool:
    """Validate a Shapely geometry object.
    
    Returns True only if:
      - not None
      - is a BaseGeometry instance
      - not empty
      - is_valid (no self-intersections)
      - has at least 1 coordinate
    """
    if geom is None:
        return False
    if not isinstance(geom, BaseGeometry):
        return False
    if geom.is_empty:
        return False
    if not geom.is_valid:
        return False

    try:
        coords = shapely.get_coordinates(geom)
        return len(coords) > 0
    except Exception:
        return False


def repair_geometry(geom: Optional[BaseGeometry]) -> Optional[BaseGeometry]:
    """Attempt to repair an invalid geometry using buffer(0).
    
    Returns original if already valid, repaired geometry if fixed, or None if unrepairable.
    """
    if geom is None or geom.is_empty:
        return None
    if geom.is_valid:
        return geom
    try:
        repaired = geom.buffer(0)
        if repaired is not None and not repaired.is_empty and repaired.is_valid:
            return repaired
    except Exception:
        pass
    return None


def simplify_safe(geom: BaseGeometry, tolerance: float, min_area_ratio: float = 0.98) -> BaseGeometry:
    """Simplify geometry safely while preserving area above min_area_ratio.
    
    If area drops below min_area_ratio * original_area, return the original geometry.
    """
    if geom is None or geom.is_empty:
        return geom
    orig_area = geom.area
    simplified = geom.simplify(tolerance, preserve_topology=True)
    if simplified is None or simplified.is_empty:
        return geom
    if orig_area > 0:
        if (simplified.area / orig_area) < min_area_ratio:
            return geom
    return simplified


def to_geojson_dict(geom: BaseGeometry) -> Dict[str, Any]:
    """Convert a Shapely geometry to a GeoJSON dict."""
    if geom is None:
        raise ValueError("Geometry cannot be None")
    return mapping(geom)


def from_geojson_dict(d: Dict[str, Any]) -> BaseGeometry:
    """Convert a GeoJSON dict to a Shapely geometry."""
    if not d or not isinstance(d, dict):
        raise ValueError("Invalid GeoJSON dictionary")
    return shape(d)
