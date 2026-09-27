"""
GeoMind AI — Export GeoJSON from PostGIS
Generates sample GeoJSON files for frontend development and demo.

Usage:
    python scripts/export_geojson.py

Outputs to data/sample/ directory.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://geomind:geomind@localhost:5432/geomind")
OUTPUT_DIR = os.path.join("data", "sample")


def export_facilities_geojson(conn):
    """Export health facilities as GeoJSON."""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT jsonb_build_object(
            'type', 'FeatureCollection',
            'metadata', jsonb_build_object(
                'generated_at', NOW(),
                'source', 'GeoMind PostGIS',
                'demo_area', 'Nairobi County'
            ),
            'features', COALESCE(jsonb_agg(
                jsonb_build_object(
                    'type', 'Feature',
                    'geometry', ST_AsGeoJSON(geom, 6)::jsonb,
                    'properties', jsonb_build_object(
                        'id', id,
                        'code', facility_code,
                        'name', name,
                        'type', facility_type,
                        'keph_level', keph_level,
                        'ownership', ownership,
                        'owner_type', owner_type,
                        'status', operational_status,
                        'subcounty', subcounty,
                        'ward', ward,
                        'beds', beds
                    )
                )
            ), '[]'::jsonb)
        ) AS geojson
        FROM health_facilities
        WHERE county ILIKE 'Nairobi'
          AND operational_status = 'Operational'
          AND geom IS NOT NULL;
    """)

    result = cur.fetchone()
    geojson = result["geojson"] if result else {"type": "FeatureCollection", "features": []}

    output_path = os.path.join(OUTPUT_DIR, "health_facilities.geojson")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2, default=str)

    feature_count = len(geojson.get("features", []))
    print(f"[OK] Facilities: {feature_count} features → {output_path}")
    cur.close()


def export_admin_boundaries_geojson(conn):
    """Export administrative boundaries as GeoJSON."""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    for level in ["county", "subcounty", "ward"]:
        cur.execute("""
            SELECT jsonb_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(jsonb_agg(
                    jsonb_build_object(
                        'type', 'Feature',
                        'geometry', ST_AsGeoJSON(geom, 6)::jsonb,
                        'properties', jsonb_build_object(
                            'id', id,
                            'name', name,
                            'level', level,
                            'code', code,
                            'area_sq_km', ROUND(area_sq_km::numeric, 2),
                            'population', population
                        )
                    )
                ), '[]'::jsonb)
            ) AS geojson
            FROM administrative_boundaries
            WHERE level = %s;
        """, (level,))

        result = cur.fetchone()
        geojson = result["geojson"] if result else {"type": "FeatureCollection", "features": []}

        output_path = os.path.join(OUTPUT_DIR, f"admin_{level}.geojson")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2, default=str)

        feature_count = len(geojson.get("features", []))
        print(f"[OK] {level}: {feature_count} features → {output_path}")

    cur.close()


def export_accessibility_geojson(conn):
    """Export accessibility results as GeoJSON (if available)."""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT COUNT(*) AS cnt FROM accessibility_results;")
    count = cur.fetchone()["cnt"]

    if count == 0:
        print("[SKIP] No accessibility results to export yet.")
        cur.close()
        return

    cur.execute("SELECT fn_accessibility_geojson() AS geojson;")
    result = cur.fetchone()
    geojson = result["geojson"] if result else {"type": "FeatureCollection", "features": []}

    output_path = os.path.join(OUTPUT_DIR, "accessibility_results.geojson")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2, default=str)

    feature_count = len(geojson.get("features", []))
    print(f"[OK] Accessibility: {feature_count} features → {output_path}")
    cur.close()


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    conn = psycopg2.connect(DATABASE_URL)

    export_facilities_geojson(conn)
    export_admin_boundaries_geojson(conn)
    export_accessibility_geojson(conn)

    conn.close()
    print(f"\n[DONE] Sample GeoJSON exported to {OUTPUT_DIR}/")
    print("Send these files to Alberto for frontend development.")


if __name__ == "__main__":
    main()
