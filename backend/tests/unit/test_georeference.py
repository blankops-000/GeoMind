import pytest
import numpy as np
from shapely.geometry import Polygon, shape
from app.services.vision.georeference import (
    pixel_to_geographic,
    bbox_to_geographic,
    mask_to_polygons,
)
from app.utils.geometry import validate_geometry

def test_pixel_to_geographic_valid():
    # Pixel polygon: (0,0) to (100,100)
    pixel_poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)])
    # Affine transform for UTM EPSG:32737 in Nairobi (approx x=250000, y=9850000)
    # col_step=10, row_step=-10
    affine = (10.0, 0.0, 250000.0, 0.0, -10.0, 9850000.0)
    
    geo_dict = pixel_to_geographic(pixel_poly, affine_transform=affine, src_crs="EPSG:32737", dst_crs="EPSG:4326")
    assert geo_dict is not None
    assert geo_dict["type"] == "Polygon"

    poly_geom = shape(geo_dict)
    assert validate_geometry(poly_geom)
    
    # Coordinates in Nairobi region
    minx, miny, maxx, maxy = poly_geom.bounds
    assert 36.0 <= minx <= 38.0
    assert -2.0 <= miny <= 0.0

def test_pixel_to_geographic_missing_affine_raises():
    pixel_poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
    with pytest.raises(ValueError):
        pixel_to_geographic(pixel_poly, affine_transform=None, src_crs="EPSG:4326")

def test_pixel_to_geographic_self_intersecting_repair():
    # Bowtie polygon (self-intersecting)
    pixel_poly = Polygon([(0, 0), (10, 10), (10, 0), (0, 10), (0, 0)])
    affine = (1.0, 0.0, 36.8, 0.0, -1.0, -1.2)
    
    geo_dict = pixel_to_geographic(pixel_poly, affine_transform=affine, src_crs="EPSG:4326")
    if geo_dict is not None:
        poly_geom = shape(geo_dict)
        assert validate_geometry(poly_geom)

def test_bbox_to_geographic():
    bbox = (0.0, 0.0, 50.0, 50.0)
    affine = (0.001, 0.0, 36.8, 0.0, -0.001, -1.28)
    geo_dict = bbox_to_geographic(bbox, affine, src_crs="EPSG:4326")
    assert geo_dict is not None
    assert geo_dict["type"] == "Polygon"

def test_mask_to_polygons():
    mask = np.zeros((50, 50), dtype=bool)
    mask[10:30, 10:30] = True
    affine = (0.001, 0.0, 36.8, 0.0, -0.001, -1.28)
    
    polys = mask_to_polygons(mask, affine, src_crs="EPSG:4326")
    assert len(polys) > 0
    for p in polys:
        assert validate_geometry(shape(p))
