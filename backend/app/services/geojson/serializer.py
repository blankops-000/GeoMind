def to_feature_collection(features: list[dict]) -> dict:
    """
    Validate and normalize a list of GeoJSON Features into
    a FeatureCollection.
    """
    normalized = []
    if isinstance(features, list):
        for f in features:
            if not isinstance(f, dict):
                continue
            if f.get("type") != "Feature":
                continue
            geom = f.get("geometry")
            if (
                not geom
                or not isinstance(geom, dict)
                or "type" not in geom
                or "coordinates" not in geom
            ):
                continue
            props = f.get("properties")
            if not isinstance(props, dict):
                props = {}
            normalized.append(
                {
                    "type": "Feature",
                    "geometry": geom,
                    "properties": props,
                }
            )
    return {
        "type": "FeatureCollection",
        "features": normalized,
    }


def simplify_feature_collection(fc: dict, max_features: int = 5000) -> dict:
    """
    If the FeatureCollection has more than max_features,
    keep the first max_features. Never break the shape.
    """
    if not isinstance(fc, dict):
        return {"type": "FeatureCollection", "features": []}
    features = fc.get("features")
    if not isinstance(features, list):
        return {"type": "FeatureCollection", "features": []}
    if len(features) <= max_features:
        return fc
    return {
        "type": "FeatureCollection",
        "features": features[:max_features],
    }


def validate_feature_collection(fc: dict) -> bool:
    if not isinstance(fc, dict):
        return False
    if fc.get("type") != "FeatureCollection":
        return False
    features = fc.get("features")
    if not isinstance(features, list):
        return False
    for f in features:
        if not isinstance(f, dict):
            return False
        if f.get("type") != "Feature":
            return False
        if "geometry" not in f or "properties" not in f:
            return False
    return True
