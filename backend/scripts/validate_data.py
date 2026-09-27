#!/usr/bin/env python3
"""GeoJSON Data Validation Script."""

import argparse
import json
import os
import sys
from typing import Dict, Any, Tuple

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import shapely
from shapely.geometry.base import BaseGeometry
from app.utils.geometry import validate_geometry, repair_geometry, from_geojson_dict


def check_coords_in_bounds(geom: BaseGeometry) -> bool:
    """Verify that all coordinates in geometry lie within valid EPSG:4326 bounds (-180..180 lon, -90..90 lat)."""
    try:
        coords = shapely.get_coordinates(geom)
        if len(coords) == 0:
            return False
        for coord in coords:
            lon, lat = float(coord[0]), float(coord[1])
            if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
                return False
        return True
    except Exception:
        return False


def validate_geojson_data(data: Dict[str, Any], attempt_repair: bool = False) -> Tuple[int, int, int, int]:
    """Validate loaded GeoJSON data dictionary.
    
    Returns tuple: (total, valid_count, invalid_count, repaired_count)
    """
    if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
        raise ValueError("GeoJSON root must be a dict with type 'FeatureCollection'")

    features = data.get("features")
    if not isinstance(features, list):
        raise ValueError("GeoJSON 'features' field must be a list")

    total = len(features)
    valid_count = 0
    invalid_count = 0
    repaired_count = 0

    for idx, feature in enumerate(features):
        if not isinstance(feature, dict):
            invalid_count += 1
            continue

        geom_dict = feature.get("geometry")
        props = feature.get("properties")

        if not geom_dict or props is None or not isinstance(props, dict):
            invalid_count += 1
            continue

        try:
            sh_geom = from_geojson_dict(geom_dict)
        except Exception:
            invalid_count += 1
            continue

        is_valid = validate_geometry(sh_geom) and check_coords_in_bounds(sh_geom)

        if is_valid:
            valid_count += 1
        elif attempt_repair:
            repaired = repair_geometry(sh_geom)
            if (
                repaired is not None
                and validate_geometry(repaired)
                and check_coords_in_bounds(repaired)
            ):
                repaired_count += 1
                valid_count += 1
            else:
                invalid_count += 1
        else:
            invalid_count += 1

    return total, valid_count, invalid_count, repaired_count


def validate_file(source_path: str, attempt_repair: bool = False) -> int:
    """Validate a GeoJSON file from path. Returns exit code (0 if valid, 1 if invalid)."""
    if not os.path.exists(source_path):
        print(f"Error: File not found at '{source_path}'")
        return 1

    try:
        with open(source_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: Failed to parse JSON file '{source_path}': {e}")
        return 1

    try:
        total, valid_count, invalid_count, repaired_count = validate_geojson_data(
            data, attempt_repair=attempt_repair
        )
    except ValueError as e:
        print(f"Error: Invalid GeoJSON structure in '{source_path}': {e}")
        return 1

    print("========================================")
    print(f"GeoJSON Validation Summary: {source_path}")
    print("========================================")
    print(f"Total features  : {total}")
    print(f"Valid features  : {valid_count}")
    print(f"Invalid features: {invalid_count}")
    print(f"Repaired        : {repaired_count}")
    print("========================================")

    if invalid_count == 0:
        print("RESULT: VALID")
        return 0
    else:
        print("RESULT: INVALID")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Validate GeoJSON file prior to data ingestion.")
    parser.add_argument("--source", required=True, help="Path to GeoJSON file to validate")
    parser.add_argument("--repair", action="store_true", help="Attempt to repair invalid geometries")
    args = parser.parse_args()

    exit_code = validate_file(args.source, attempt_repair=args.repair)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
