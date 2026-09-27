"""Coordinate Reference System (CRS) transformation utilities."""

from typing import Any, Dict, Union
import pyproj
from pyproj import CRS, Transformer
import shapely.ops
from shapely.geometry import Polygon, shape, mapping
from shapely.geometry.base import BaseGeometry

DEFAULT_SRID = 4326


def _parse_crs(crs_input: Union[int, str, CRS]) -> CRS:
    if isinstance(crs_input, CRS):
        return crs_input
    if isinstance(crs_input, int):
        return CRS.from_epsg(crs_input)
    if isinstance(crs_input, str):
        if crs_input.isdigit():
            return CRS.from_epsg(int(crs_input))
        return CRS.from_user_input(crs_input)
    raise ValueError(f"Invalid CRS input: {crs_input}")


def transform_geom(geom: BaseGeometry, src_crs: Union[int, str, CRS], dst_crs: Union[int, str, CRS]) -> BaseGeometry:
    """Transform a Shapely geometry from src_crs to dst_crs."""
    if geom is None or geom.is_empty:
        raise ValueError("Cannot transform null or empty geometry")
    src = _parse_crs(src_crs)
    dst = _parse_crs(dst_crs)
    if src == dst:
        return geom
    transformer = Transformer.from_crs(src, dst, always_xy=True)
    return shapely.ops.transform(transformer.transform, geom)


def to_4326(geom: BaseGeometry, src_crs: Union[int, str, CRS]) -> BaseGeometry:
    """Transform geometry from src_crs to EPSG:4326 (WGS84)."""
    if geom is None:
        raise ValueError("Geometry cannot be None")
    return transform_geom(geom, src_crs, DEFAULT_SRID)


def to_utm(geom: BaseGeometry, utm_epsg: int) -> BaseGeometry:
    """Transform geometry from EPSG:4326 to specified UTM EPSG code."""
    if geom is None:
        raise ValueError("Geometry cannot be None")
    if not isinstance(utm_epsg, int):
        raise ValueError("utm_epsg must be an integer EPSG code")
    return transform_geom(geom, DEFAULT_SRID, utm_epsg)


def bbox_to_polygon(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> Polygon:
    """Create a Shapely Polygon representing a bounding box in EPSG:4326."""
    if min_lon > max_lon or min_lat > max_lat:
        raise ValueError(f"Invalid bbox bounds: min bounds ({min_lon}, {min_lat}) exceed max bounds ({max_lon}, {max_lat})")
    if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180 and -90 <= min_lat <= 90 and -90 <= max_lat <= 90):
        raise ValueError(f"Coordinates out of bounds for EPSG:4326: ({min_lon}, {min_lat}, {max_lon}, {max_lat})")
    return Polygon([
        (min_lon, min_lat),
        (max_lon, min_lat),
        (max_lon, max_lat),
        (min_lon, max_lat),
        (min_lon, min_lat)
    ])


def transform_geojson(geojson_dict: Dict[str, Any], src_srid: Union[int, str], dst_srid: Union[int, str]) -> Dict[str, Any]:
    """Transform a GeoJSON dictionary (FeatureCollection, Feature, or Geometry) from src_srid to dst_srid."""
    if not isinstance(geojson_dict, dict):
        raise ValueError("geojson_dict must be a dictionary")
    if "type" not in geojson_dict:
        raise ValueError("Invalid GeoJSON dict: missing 'type'")

    g_type = geojson_dict.get("type")
    if g_type == "FeatureCollection":
        transformed_features = []
        for feature in geojson_dict.get("features", []):
            transformed_features.append(transform_geojson(feature, src_srid, dst_srid))
        res = dict(geojson_dict)
        res["features"] = transformed_features
        return res
    elif g_type == "Feature":
        geom_dict = geojson_dict.get("geometry")
        if not geom_dict:
            return geojson_dict
        sh_geom = shape(geom_dict)
        transformed_geom = transform_geom(sh_geom, src_srid, dst_srid)
        res = dict(geojson_dict)
        res["geometry"] = mapping(transformed_geom)
        return res
    else:
        # Geometry object
        sh_geom = shape(geojson_dict)
        transformed_geom = transform_geom(sh_geom, src_srid, dst_srid)
        return mapping(transformed_geom)
