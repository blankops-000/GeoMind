import pytest
from app.services.geojson.serializer import (
    to_feature_collection,
    simplify_feature_collection,
    validate_feature_collection,
)


def test_to_feature_collection_valid():
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [36.8, -1.2]},
            "properties": {"name": "Nairobi"},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
            },
            "properties": {"id": 1},
        },
    ]
    fc = to_feature_collection(features)
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 2
    assert fc["features"][0]["geometry"]["type"] == "Point"
    assert fc["features"][1]["properties"]["id"] == 1


def test_to_feature_collection_invalid_skips():
    features = [
        "not a dict",
        {"type": "NotAFeature"},
        {"type": "Feature", "geometry": None},
        {"type": "Feature", "geometry": {"type": "Point"}},  # missing coordinates
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [36.8, -1.2]},
            "properties": None,  # should default to dict
        },
    ]
    fc = to_feature_collection(features)
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 1
    assert fc["features"][0]["properties"] == {}


def test_validate_feature_collection_valid():
    fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "properties": {},
            }
        ],
    }
    assert validate_feature_collection(fc) is True


def test_validate_feature_collection_garbage():
    assert validate_feature_collection(None) is False
    assert validate_feature_collection({}) is False
    assert validate_feature_collection({"type": "Invalid"}) is False
    assert validate_feature_collection({"type": "FeatureCollection", "features": "not a list"}) is False
    assert validate_feature_collection(
        {
            "type": "FeatureCollection",
            "features": [
                {"type": "InvalidFeature", "geometry": {}, "properties": {}}
            ],
        }
    ) is False
    assert validate_feature_collection(
        {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": {}}  # missing geometry
            ],
        }
    ) is False


def test_simplify_feature_collection_cap():
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [i, i]},
            "properties": {"idx": i},
        }
        for i in range(10)
    ]
    fc = {"type": "FeatureCollection", "features": features}

    simplified = simplify_feature_collection(fc, max_features=5)
    assert len(simplified["features"]) == 5
    assert simplified["features"][4]["properties"]["idx"] == 4

    unmodified = simplify_feature_collection(fc, max_features=20)
    assert len(unmodified["features"]) == 10
