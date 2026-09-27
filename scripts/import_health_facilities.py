"""
GeoMind AI — Import Health Facilities from KMHFR
Downloads health facilities for Nairobi County from the Kenya Master
Health Facility Registry ArcGIS FeatureServer and loads them into PostGIS.

Usage:
    python scripts/import_health_facilities.py

Idempotent: Uses UPSERT (ON CONFLICT) so safe to re-run.
"""

import os
import sys
import json
import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://geomind:geomind@localhost:5432/geomind")

# KMHFR ArcGIS FeatureServer endpoint
ARCGIS_BASE_URL = (
    "https://services5.arcgis.com/XGXQEX3dSjCZQoLu/arcgis/rest/services/"
    "KMHFR_Health_Facilities/FeatureServer/0/query"
)

# Nairobi County bounding box for validation
NAIROBI_BBOX = {
    "min_lon": 36.65,
    "max_lon": 37.10,
    "min_lat": -1.45,
    "max_lat": -1.15,
}


def fetch_facilities(county="Nairobi"):
    """Fetch health facilities from KMHFR ArcGIS FeatureServer."""
    print(f"[INFO] Fetching health facilities for {county} County...")

    all_features = []
    offset = 0
    batch_size = 1000

    while True:
        params = {
            "where": f"County='{county}'",
            "outFields": "*",
            "outSR": "4326",
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": batch_size,
        }

        try:
            response = requests.get(ARCGIS_BASE_URL, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"[ERROR] Failed to fetch from ArcGIS: {e}")
            # Fall back to local file if available
            local_path = os.path.join("data", "raw", "health_facilities_nairobi.geojson")
            if os.path.exists(local_path):
                print(f"[INFO] Loading from local file: {local_path}")
                with open(local_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("features", [])
            sys.exit(1)

        features = data.get("features", [])
        if not features:
            break

        all_features.extend(features)
        print(f"  Fetched {len(features)} features (total: {len(all_features)})")

        if len(features) < batch_size:
            break
        offset += batch_size

    # Save raw data
    raw_path = os.path.join("data", "raw", "health_facilities_nairobi.geojson")
    os.makedirs(os.path.dirname(raw_path), exist_ok=True)
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": all_features}, f)
    print(f"[INFO] Raw data saved to {raw_path}")

    return all_features


def clean_facilities(features):
    """Clean and validate facility records."""
    print(f"[INFO] Cleaning {len(features)} features...")

    cleaned = []
    skipped = {"no_coords": 0, "outside_bbox": 0, "duplicate": 0}
    seen_codes = set()

    for feat in features:
        props = feat.get("properties", {})
        geom = feat.get("geometry", {})

        # Skip if no geometry
        if not geom or not geom.get("coordinates"):
            skipped["no_coords"] += 1
            continue

        lon, lat = geom["coordinates"][0], geom["coordinates"][1]

        # Validate coordinates are within Nairobi
        if not (
            NAIROBI_BBOX["min_lon"] <= lon <= NAIROBI_BBOX["max_lon"]
            and NAIROBI_BBOX["min_lat"] <= lat <= NAIROBI_BBOX["max_lat"]
        ):
            skipped["outside_bbox"] += 1
            continue

        # Deduplicate by facility code
        facility_code = props.get("Facility_Code") or props.get("facility_code") or props.get("Code")
        if facility_code:
            facility_code = str(facility_code).strip()
            if facility_code in seen_codes:
                skipped["duplicate"] += 1
                continue
            seen_codes.add(facility_code)

        record = {
            "facility_code": facility_code,
            "name": (props.get("Facility_Name") or props.get("Official_Name") or props.get("name") or "Unknown").strip(),
            "facility_type": props.get("Facility_Type") or props.get("Keph_level") or None,
            "keph_level": props.get("Keph_Level") or props.get("Keph_level") or None,
            "ownership": props.get("Owner") or props.get("owner") or None,
            "owner_type": props.get("Owner_Type") or props.get("owner_type") or None,
            "operational_status": props.get("Operation_Status") or props.get("Operational") or "Operational",
            "county": props.get("County") or "Nairobi",
            "subcounty": props.get("Sub_County") or props.get("Sub_county") or None,
            "ward": props.get("Ward") or props.get("ward") or None,
            "constituency": props.get("Constituency") or None,
            "latitude": lat,
            "longitude": lon,
            "beds": props.get("Beds") or props.get("Total_Beds") or None,
            "cots": props.get("Cots") or props.get("Total_Cots") or None,
        }
        cleaned.append(record)

    print(f"[INFO] Cleaned: {len(cleaned)} valid records")
    print(f"  Skipped — no coordinates: {skipped['no_coords']}")
    print(f"  Skipped — outside Nairobi: {skipped['outside_bbox']}")
    print(f"  Skipped — duplicate code: {skipped['duplicate']}")

    return cleaned


def load_to_postgis(records):
    """Insert facility records into PostGIS with UPSERT."""
    print(f"[INFO] Loading {len(records)} facilities into PostGIS...")

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    insert_sql = """
        INSERT INTO health_facilities (
            facility_code, name, facility_type, keph_level, ownership, owner_type,
            operational_status, county, subcounty, ward, constituency,
            latitude, longitude, beds, cots,
            source, date_acquired, geom
        ) VALUES %s
        ON CONFLICT (facility_code) DO UPDATE SET
            name = EXCLUDED.name,
            facility_type = EXCLUDED.facility_type,
            keph_level = EXCLUDED.keph_level,
            ownership = EXCLUDED.ownership,
            owner_type = EXCLUDED.owner_type,
            operational_status = EXCLUDED.operational_status,
            subcounty = EXCLUDED.subcounty,
            ward = EXCLUDED.ward,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            beds = EXCLUDED.beds,
            cots = EXCLUDED.cots,
            geom = EXCLUDED.geom;
    """

    values = []
    for r in records:
        values.append((
            r["facility_code"],
            r["name"],
            r["facility_type"],
            r["keph_level"],
            r["ownership"],
            r["owner_type"],
            r["operational_status"],
            r["county"],
            r["subcounty"],
            r["ward"],
            r["constituency"],
            r["latitude"],
            r["longitude"],
            r["beds"],
            r["cots"],
            "KMHFR",
            "2026-09-27",
            f"SRID=4326;POINT({r['longitude']} {r['latitude']})",
        ))

    template = (
        "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_GeomFromEWKT(%s))"
    )

    execute_values(cur, insert_sql, values, template=template, page_size=500)
    conn.commit()

    # Verify
    cur.execute("SELECT COUNT(*) FROM health_facilities WHERE county ILIKE 'Nairobi';")
    count = cur.fetchone()[0]
    print(f"[SUCCESS] {count} Nairobi facilities now in PostGIS")

    cur.close()
    conn.close()


def main():
    features = fetch_facilities("Nairobi")
    if not features:
        print("[ERROR] No features fetched. Check the API or local fallback file.")
        sys.exit(1)

    records = clean_facilities(features)
    if not records:
        print("[ERROR] No valid records after cleaning.")
        sys.exit(1)

    load_to_postgis(records)
    print("[DONE] Health facilities import complete.")


if __name__ == "__main__":
    main()
