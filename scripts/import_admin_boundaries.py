"""
GeoMind AI — Import Administrative Boundaries
Downloads Kenya admin boundaries from HDX (Humanitarian Data Exchange)
and loads Nairobi County hierarchy into PostGIS.

Usage:
    python scripts/import_admin_boundaries.py

Idempotent: Clears and reloads Nairobi boundaries.
"""

import os
import sys
import json
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://geomind:geomind@localhost:5432/geomind")

# HDX dataset URLs for Kenya admin boundaries
# These may change — check https://data.humdata.org/dataset/cod-ab-ken
HDX_SOURCES = {
    "county": "https://data.humdata.org/dataset/cod-ab-ken/resource/kenya_admin1.geojson",
    "subcounty": "https://data.humdata.org/dataset/cod-ab-ken/resource/kenya_admin2.geojson",
    "ward": "https://data.humdata.org/dataset/cod-ab-ken/resource/kenya_admin3.geojson",
}

# Fallback: direct download links (update as needed)
FALLBACK_URLS = {
    "county": "https://raw.githubusercontent.com/mikelmaron/kenya-election-data/master/data/counties.geojson",
}


def fetch_boundaries(level, url):
    """Fetch GeoJSON boundaries from a URL."""
    print(f"[INFO] Fetching {level} boundaries from {url}...")

    local_path = os.path.join("data", "raw", f"admin_{level}_kenya.geojson")

    # Try local file first
    if os.path.exists(local_path):
        print(f"[INFO] Loading from local file: {local_path}")
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)

    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        data = response.json()

        # Save raw
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        print(f"[INFO] Saved to {local_path}")

        return data
    except requests.RequestException as e:
        print(f"[WARN] Failed to fetch {level}: {e}")
        return None


def filter_nairobi(geojson_data, level):
    """Filter features to Nairobi County."""
    features = geojson_data.get("features", [])
    nairobi_features = []

    name_fields = {
        "county": ["ADM1_EN", "COUNTY", "admin1Name", "name", "NAME"],
        "subcounty": ["ADM2_EN", "SUBCOUNTY", "admin2Name", "name", "NAME"],
        "ward": ["ADM3_EN", "WARD", "admin3Name", "name", "NAME"],
    }

    county_fields = ["ADM1_EN", "COUNTY", "admin1Name", "county"]

    for feat in features:
        props = feat.get("properties", {})

        # Check if this feature belongs to Nairobi
        is_nairobi = False
        if level == "county":
            for field in name_fields["county"]:
                val = props.get(field, "")
                if val and "nairobi" in str(val).lower():
                    is_nairobi = True
                    break
        else:
            for field in county_fields:
                val = props.get(field, "")
                if val and "nairobi" in str(val).lower():
                    is_nairobi = True
                    break

        if is_nairobi:
            # Extract the name
            name = None
            for field in name_fields.get(level, []):
                if props.get(field):
                    name = str(props[field]).strip()
                    break
            if not name:
                name = f"Unknown {level}"

            # Extract code
            code = None
            for field in ["ADM1_PCODE", "ADM2_PCODE", "ADM3_PCODE", "admin_code", "code"]:
                if props.get(field):
                    code = str(props[field]).strip()
                    break

            feat["_parsed"] = {"name": name, "code": code}
            nairobi_features.append(feat)

    print(f"[INFO] {level}: {len(nairobi_features)} Nairobi features found")
    return nairobi_features


def load_boundaries(features, level, conn):
    """Insert boundary features into PostGIS."""
    cur = conn.cursor()

    for feat in features:
        parsed = feat.get("_parsed", {})
        name = parsed.get("name", "Unknown")
        code = parsed.get("code")
        geom_json = json.dumps(feat["geometry"])

        # Ensure MultiPolygon
        cur.execute("""
            INSERT INTO administrative_boundaries (name, level, code, geom)
            VALUES (
                %s, %s, %s,
                ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
            )
            ON CONFLICT (code) DO UPDATE SET
                name = EXCLUDED.name,
                geom = EXCLUDED.geom;
        """, (name, level, code, geom_json))

    conn.commit()
    cur.close()
    print(f"[INFO] Loaded {len(features)} {level} boundaries into PostGIS")


def update_parent_ids(conn):
    """Set parent_id based on spatial containment."""
    cur = conn.cursor()

    # Sub-counties → parent county
    cur.execute("""
        UPDATE administrative_boundaries sc
        SET parent_id = c.id
        FROM administrative_boundaries c
        WHERE sc.level = 'subcounty'
          AND c.level = 'county'
          AND ST_Within(ST_Centroid(sc.geom), c.geom);
    """)

    # Wards → parent sub-county
    cur.execute("""
        UPDATE administrative_boundaries w
        SET parent_id = sc.id
        FROM administrative_boundaries sc
        WHERE w.level = 'ward'
          AND sc.level = 'subcounty'
          AND ST_Within(ST_Centroid(w.geom), sc.geom);
    """)

    conn.commit()
    cur.close()
    print("[INFO] Parent-child hierarchy updated")


def update_area(conn):
    """Compute area_sq_km from geometry."""
    cur = conn.cursor()
    cur.execute("""
        UPDATE administrative_boundaries
        SET area_sq_km = ST_Area(geom::geography) / 1000000.0;
    """)
    conn.commit()
    cur.close()
    print("[INFO] Areas computed")


def main():
    conn = psycopg2.connect(DATABASE_URL)

    for level, url in HDX_SOURCES.items():
        data = fetch_boundaries(level, url)
        if not data:
            fallback = FALLBACK_URLS.get(level)
            if fallback:
                data = fetch_boundaries(level, fallback)
        if not data:
            print(f"[WARN] Skipping {level} — no data available")
            continue

        features = filter_nairobi(data, level)
        if features:
            load_boundaries(features, level, conn)

    update_parent_ids(conn)
    update_area(conn)

    # Summary
    cur = conn.cursor()
    for level in ["county", "subcounty", "ward"]:
        cur.execute(
            "SELECT COUNT(*) FROM administrative_boundaries WHERE level = %s;",
            (level,),
        )
        count = cur.fetchone()[0]
        print(f"  {level}: {count} records")
    cur.close()

    conn.close()
    print("[DONE] Administrative boundaries import complete.")


if __name__ == "__main__":
    main()
