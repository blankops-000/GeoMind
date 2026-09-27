import sys
from sqlalchemy import text
from app.core.config import settings
from app.db.session import engine


def seed_demo():
    print(f"Seeding demo data into database at {settings.DATABASE_URL}...")

    bbox_parts = [float(x.strip()) for x in settings.DEMO_BBOX.split(",")]
    if len(bbox_parts) != 4:
        raise ValueError(f"Invalid DEMO_BBOX format: {settings.DEMO_BBOX}")

    min_lon, min_lat, max_lon, max_lat = bbox_parts

    wkt_multipoly = (
        f"MULTIPOLYGON((({min_lon} {min_lat}, {max_lon} {min_lat}, "
        f"{max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat})))"
    )

    categories = ["clinic", "hospital", "health_center"]

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Clean existing demo rows for idempotency
            conn.execute(text("DELETE FROM facilities WHERE name LIKE 'Demo Health Facility%';"))
            conn.execute(text("DELETE FROM geographic_regions WHERE name = 'Demo Region' AND region_type = 'demo';"))
            conn.execute(text("DELETE FROM datasets WHERE name = 'demo_region';"))

            # 2. Insert Dataset
            insert_dataset = text("""
                INSERT INTO datasets (name, source, crs, description)
                VALUES ('demo_region', 'synthetic', 'EPSG:4326', 'Synthetic demo region dataset')
                ON CONFLICT (name) DO UPDATE SET source = EXCLUDED.source;
            """)
            conn.execute(insert_dataset)

            # 3. Insert Geographic Region
            insert_region = text("""
                INSERT INTO geographic_regions (name, region_type, geom, attributes)
                VALUES ('Demo Region', 'demo', ST_GeomFromText(:wkt, 4326), '{"demo": true}'::jsonb);
            """)
            conn.execute(insert_region, {"wkt": wkt_multipoly})

            # 4. Insert 10 Facilities
            insert_facility = text("""
                INSERT INTO facilities (name, feature_type, category, source_id, geom, attributes)
                VALUES (:name, 'health_facility', :category, :source_id, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), '{"demo": true}'::jsonb);
            """)

            inserted_facilities = 0
            for i in range(10):
                ratio = i / 9.0 if 9.0 > 0 else 0.5
                lon = min_lon + (max_lon - min_lon) * (0.1 + 0.8 * ratio)
                lat = min_lat + (max_lat - min_lat) * (0.1 + 0.8 * (1.0 - ratio))
                cat = categories[i % len(categories)]
                facility_name = f"Demo Health Facility {i+1}"
                source_id = f"demo-{i+1}"

                conn.execute(insert_facility, {
                    "name": facility_name,
                    "category": cat,
                    "source_id": source_id,
                    "lon": lon,
                    "lat": lat,
                })
                inserted_facilities += 1

            trans.commit()
            print("Seeding complete successfully:")
            print("  - 1 dataset inserted ('demo_region')")
            print("  - 1 geographic region inserted ('Demo Region')")
            print(f"  - {inserted_facilities} facilities inserted ('health_facility')")

        except Exception as e:
            trans.rollback()
            raise e


if __name__ == "__main__":
    try:
        seed_demo()
        sys.exit(0)
    except Exception as e:
        print(f"Seeding failed: {e}", file=sys.stderr)
        sys.exit(1)
