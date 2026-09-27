"""Unit tests for app.utils.geometry module."""

import pytest
from shapely.geometry import Polygon, Point, MultiPolygon
from app.utils.geometry import (
    validate_geometry,
    repair_geometry,
    simplify_safe,
    to_geojson_dict,
    from_geojson_dict,
)


def test_validate_geometry_valid_polygon():
    valid_poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    assert validate_geometry(valid_poly) is True


def test_validate_geometry_self_intersecting():
    # Bowtie polygon (self-intersecting shape)
    invalid_poly = Polygon([(0, 0), (0, 2), (1, 1), (2, 2), (2, 0), (1, 1), (0, 0)])
    assert validate_geometry(invalid_poly) is False


def test_validate_geometry_none_and_empty():
    assert validate_geometry(None) is False
    assert validate_geometry(Polygon()) is False


def test_repair_geometry_valid_returns_same():
    valid_poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    repaired = repair_geometry(valid_poly)
    assert repaired is not None
    assert validate_geometry(repaired) is True


def test_repair_geometry_invalid_returns_valid_or_none():
    invalid_poly = Polygon([(0, 0), (0, 2), (1, 1), (2, 2), (2, 0), (1, 1), (0, 0)])
    repaired = repair_geometry(invalid_poly)
    if repaired is not None:
        assert validate_geometry(repaired) is True


def test_simplify_safe_preserves_area_within_tolerance():
    # Square with a slight bump along one side
    coords = [(0, 0), (5, 0), (5, 5), (2.5, 5.05), (0, 5), (0, 0)]
    poly = Polygon(coords)
    orig_area = poly.area

    # Simplify with small tolerance
    simplified = simplify_safe(poly, tolerance=0.1, min_area_ratio=0.98)
    assert simplified is not None
    assert simplified.area / orig_area >= 0.98


def test_simplify_safe_reverts_if_area_drops_excessively():
    # A polygon with a fine structure where simplification reduces area significantly
    poly = Polygon([(0, 0), (10, 0), (10, 1), (1, 1), (1, 10), (0, 10), (0, 0)])
    orig_area = poly.area

    # Aggressive simplification that would collapse area
    simplified = simplify_safe(poly, tolerance=20.0, min_area_ratio=0.98)
    assert simplified.area == orig_area


def test_geojson_dict_round_trip():
    pt = Point(36.82, -1.29)
    g_dict = to_geojson_dict(pt)
    assert g_dict == {"type": "Point", "coordinates": (36.82, -1.29)}

    reconstructed = from_geojson_dict(g_dict)
    assert reconstructed.equals(pt)
