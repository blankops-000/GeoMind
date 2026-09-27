"""
GeoMind AI — Import Roads from OpenStreetMap
Downloads road network for Nairobi County via Overpass API
and loads into PostGIS.

Usage:
    python scripts/import_roads.py

Idempotent: Uses UPSERT on osm_id.
"""

import os
import sys
import json
import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://geomind:geomind@localhost:5432/geomind")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Road classes to import (skip footpaths, tracks, service roads for MVP)
ROAD_CLASSES = [
    "motorway", "motorway_link",
    "trunk", "trunk_link",
    "primary", "primary_link",
    "secondary", "secondary_link",
    "tertiary", "tertiary_link",
    "residential",
    "unclassified",
]

# Overpass query for Nairobi County roads
OVERPASS_QUERY = """
[out:json][timeout:180];
area["name"="Nairobi"]["admin_level"="4"]->.searchArea;
(
  way["highway"~"^(motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|residential|unclassified)$"](area.searchArea);
);
out body;
>;
out skel qt;
"""


def fetch_roads():
    """Fetch road network from Overpass API."""
    print("[INFO] Fetching Nairobi road network from Overpass API...")
    print("  This may take 1-2 minutes...")

    local_path = os.path.join("data", "raw", "roads_nairobi_osm.json")

    # Try local cache first
    if os.path.exists(local_path):
        print(f"[INFO] Loading from cache: {local_path}")
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)

    try:
        response = requests.post(
            OVERPASS_URL,
            data={"data": OVERPASS_QUERY},
            timeout=300,
        )
        response.raise_for_status()
        data = response.json()

        # Cache raw response
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        print(f"[INFO] Cached to {local_path}")

        return data
    except requests.RequestException as e:
        print(f"[ERROR] Overpass API failed: {e}")
        sys.exit(1)


def osm_to_linestrings(data):
    """Convert Overpass JSON to list of road records with WKT geometries."""
    elements = data.get("elements", [])

    # Build node lookup: id → (lon, lat)
    nodes = {}
    ways = []
    for el in elements:
        if el["type"] == "node":
            nodes[el["id"]] = (el["lon"], el["lat"])
        elif el["type"] == "way":
            ways.append(el)

    print(f"[INFO] Parsed {len(nodes)} nodes and {len(ways)} ways")

    records = []
    for way in ways:
        tags = way.get("tags", {})
        road_class = tags.get("highway")

        if road_class not in ROAD_CLASSES:
            continue

        # Build coordinate list
        coords = []
        for node_id in way.get("nodes", []):
            if node_id in nodes:
                coords.append(nodes[node_id])

        if len(coords) < 2:
            continue

        # Build WKT LineString
        coord_str = ", ".join(f"{lon} {lat}" for lon, lat in coords)
        wkt = f"SRID=4326;LINESTRING({coord_str})"

        records.append({
            "osm_id": way["id"],
            "name": tags.get("name"),
            "road_class": road_class,
            "surface": tags.get("surface"),
            "lanes": tags.get("lanes"),
            "oneway": tags.get("oneway") == "yes",
            "wkt": wkt,
        })

    print(f"[INFO] Converted {len(records)} road segments")
    return records


def load_to_postgis(records):
    """Insert road records into PostGIS."""
    print(f"[INFO] Loading {len(records)} roads into PostGIS...")

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Batch insert
    batch_size = 1000
    loaded = 0

    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]

        for r in batch:
            lanes = None
            if r["lanes"]:
                try:
                    lanes = int(r["lanes"])
                except (ValueError, TypeError):
                    lanes = None

            cur.execute("""
                INSERT INTO roads (osm_id, name, road_class, surface, lanes, oneway, geom)
                VALUES (%s, %s, %s, %s, %s, %s, ST_GeomFromEWKT(%s))
                ON CONFLICT (osm_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    road_class = EXCLUDED.road_class,
                    surface = EXCLUDED.surface,
                    lanes = EXCLUDED.lanes,
                    geom = EXCLUDED.geom;
            """, (
                r["osm_id"],
                r["name"],
                r["road_class"],
                r["surface"],
                lanes,
                r["oneway"],
                r["wkt"],
            ))

        conn.commit()
        loaded += len(batch)
        print(f"  Loaded {loaded}/{len(records)} roads")

    # Compute lengths
    cur.execute("""
        UPDATE roads SET length_meters = ST_Length(geom::geography)
        WHERE length_meters IS NULL;
    """)
    conn.commit()

    # Summary
    cur.execute("SELECT COUNT(*), ROUND(SUM(length_meters)/1000, 1) FROM roads;")
    count, total_km = cur.fetchone()
    print(f"[SUCCESS] {count} road segments loaded ({total_km} km total)")

    cur.execute("""
        SELECT road_class, COUNT(*) as cnt
        FROM roads
        GROUP BY road_class
        ORDER BY cnt DESC;
    """)
    print("  Road class breakdown:")
    for row in cur.fetchall():
        print(f"    {row[0]}: {row[1]}")

    cur.close()
    conn.close()


def main():
    data = fetch_roads()
    records = osm_to_linestrings(data)

    if not records:
        print("[ERROR] No road segments extracted.")
        sys.exit(1)

    load_to_postgis(records)
    print("[DONE] Roads import complete.")


if __name__ == "__main__":
    main()
