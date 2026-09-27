"""Unit tests for app.utils.crs module."""

import pytest
from shapely.geometry import Point, Polygon
from app.utils.crs import (
    DEFAULT_SRID,
    bbox_to_polygon,
    to_4326,
    to_utm,
    transform_geojson,
)


def test_bbox_to_polygon_returns_correct_bounds():
    poly = bbox_to_polygon(36.5, -1.5, 37.0, -1.1)
    assert isinstance(poly, Polygon)
    bounds = poly.bounds
    assert bounds == (36.5, -1.5, 37.0, -1.1)


def test_bbox_to_polygon_invalid_bounds_raises_value_error():
    with pytest.raises(ValueError):
        bbox_to_polygon(37.0, -1.5, 36.5, -1.1)

    with pytest.raises(ValueError):
        bbox_to_polygon(200.0, -1.5, 37.0, -1.1)


def test_to_4326_and_to_utm_round_trip():
    # Nairobi point in EPSG:4326 (WGS84)
    pt = Point(36.8219, -1.2921)
    
    # UTM Zone 37S for Nairobi EPSG:32737
    utm_epsg = 32737
    
    pt_utm = to_utm(pt, utm_epsg)
    assert pt_utm is not None
    assert not pt_utm.equals(pt)

    # Round trip back to 4326
    pt_4326 = to_4326(pt_utm, utm_epsg)
    assert pytest.approx(pt_4326.x, abs=1e-5) == pt.x
    assert pytest.approx(pt_4326.y, abs=1e-5) == pt.y


def test_transform_geojson_transforms_point():
    geojson_pt = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [36.8219, -1.2921]
        },
        "properties": {"name": "Test Point"}
    }

    utm_epsg = 32737
    transformed = transform_geojson(geojson_pt, DEFAULT_SRID, utm_epsg)
    
    assert transformed["type"] == "Feature"
    assert transformed["properties"] == {"name": "Test Point"}
    coords = transformed["geometry"]["coordinates"]
    assert coords[0] != 36.8219
    assert coords[1] != -1.2921

    # Reverse transformation
    reversed_pt = transform_geojson(transformed, utm_epsg, DEFAULT_SRID)
    rev_coords = reversed_pt["geometry"]["coordinates"]
    assert pytest.approx(rev_coords[0], abs=1e-5) == 36.8219
    assert pytest.approx(rev_coords[1], abs=1e-5) == -1.2921
