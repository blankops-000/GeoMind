from __future__ import annotations
from typing import Optional, Any, Literal
from pydantic import BaseModel

class Geometry(BaseModel):
    type: Literal[
        "Point", "LineString", "Polygon",
        "MultiPoint", "MultiLineString", "MultiPolygon"
    ]
    coordinates: Any

class Feature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: Geometry
    properties: dict[str, Any] = {}

class FeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[Feature] = []
