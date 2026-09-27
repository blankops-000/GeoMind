#!/usr/bin/env python3
"""GeoJSON Data Import Script into GeoMind PostgreSQL/PostGIS Database."""

import argparse
import json
import os
import sys
from typing import Any, Dict

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from geoalchemy2.shape import from_shape
from app.db.session import SessionLocal
from app.db.models import Facility, GeographicRegion, Dataset
from app.utils.geometry import from_geojson_dict
from scripts.validate_data import validate_geojson_data


def import_data(
    source_path: str,
    table: str,
    feature_type: str,
    dataset_name: str = None,
    reset: bool = False,
) -> int:
    """Import features from a GeoJSON file into the PostgreSQL database.
    
    Returns exit code (0 on success, 1 on error).
    """
    if not os.path.exists(source_path):
        print(f"Error: File not found at '{source_path}'")
        return 1

    try:
        with open(source_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: Failed to parse JSON file '{source_path}': {e}")
        return 1

    # 1. Validate GeoJSON
    try:
        total, valid_count, invalid_count, _ = validate_geojson_data(data)
        if invalid_count > 0:
            print(f"Error: Data validation failed ({invalid_count} invalid features out of {total}). Aborting import.")
            return 1
    except Exception as e:
        print(f"Error validating GeoJSON data: {e}")
        return 1

    if not dataset_name:
        dataset_name = os.path.splitext(os.path.basename(source_path))[0]

    # Normalize table name
    target_table = table.lower().strip()
    if target_table in ["regions", "geographic_regions"]:
        target_table = "geographic_regions"
    elif target_table in ["facilities", "facility"]:
        target_table = "facilities"
    else:
        print(f"Error: Invalid table parameter '{table}'. Must be 'facilities' or 'regions'.")
        return 1

    db = SessionLocal()
    inserted_count = 0
    skipped_count = 0
    failed_count = 0

    try:
        # 2. Register Dataset row if missing
        ds = db.query(Dataset).filter(Dataset.name == dataset_name).first()
        if not ds:
            ds = Dataset(
                name=dataset_name,
                source="local_file",
                crs="EPSG:4326",
                description=f"Imported from {os.path.basename(source_path)}"
            )
            db.add(ds)
            db.commit()

        # 3. Handle --reset flag
        if reset:
            if target_table == "facilities":
                db.query(Facility).filter(Facility.feature_type == feature_type).delete(synchronize_session=False)
            elif target_table == "geographic_regions":
                db.query(GeographicRegion).filter(GeographicRegion.region_type == feature_type).delete(synchronize_session=False)
            db.commit()

        # 4. Insert features
        features = data.get("features", [])
        for feat in features:
            try:
                geom_dict = feat.get("geometry")
                props = feat.get("properties", {})

                sh_geom = from_geojson_dict(geom_dict)
                geom_elem = from_shape(sh_geom, srid=4326)

                if target_table == "geographic_regions":
                    name = props.get("name", dataset_name)
                    r_type = props.get("region_type", feature_type)
                    parent_id = props.get("parent_id")
                    extra_attrs = {
                        k: v for k, v in props.items()
                        if k not in ["name", "region_type", "parent_id"]
                    }
                    region = GeographicRegion(
                        name=name,
                        region_type=r_type,
                        parent_id=parent_id,
                        attributes=extra_attrs,
                        geom=geom_elem
                    )
                    db.add(region)
                elif target_table == "facilities":
                    name = props.get("name", "Facility")
                    f_type = feature_type
                    category = props.get("category")
                    source_id = str(props["source_id"]) if "source_id" in props and props["source_id"] is not None else (str(props["id"]) if "id" in props and props["id"] is not None else None)
                    extra_attrs = {
                        k: v for k, v in props.items()
                        if k not in ["name", "feature_type", "category", "source_id", "id"]
                    }
                    facility = Facility(
                        name=name,
                        feature_type=f_type,
                        category=category,
                        source_id=source_id,
                        attributes=extra_attrs,
                        geom=geom_elem
                    )
                    db.add(facility)

                inserted_count += 1
            except Exception as e:
                print(f"Warning: Failed to process feature: {e}")
                failed_count += 1

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Error during import: {e}")
        return 1
    finally:
        db.close()

    print("========================================")
    print(f"GeoJSON Import Summary: {source_path}")
    print("========================================")
    print(f"Table         : {target_table}")
    print(f"Feature Type  : {feature_type}")
    print(f"Inserted      : {inserted_count}")
    print(f"Skipped       : {skipped_count}")
    print(f"Failed        : {failed_count}")
    print("========================================")

    return 0 if failed_count == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Import GeoJSON dataset into GeoMind database.")
    parser.add_argument("--source", required=True, help="Path to GeoJSON source file")
    parser.add_argument("--table", required=True, choices=["facilities", "regions", "geographic_regions"], help="Target DB table")
    parser.add_argument("--type", required=True, help="Feature type or region type identifier")
    parser.add_argument("--name", help="Optional dataset name override")
    parser.add_argument("--reset", action="store_true", help="Delete existing features with matching type before importing")
    args = parser.parse_args()

    exit_code = import_data(
        source_path=args.source,
        table=args.table,
        feature_type=args.type,
        dataset_name=args.name,
        reset=args.reset
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
