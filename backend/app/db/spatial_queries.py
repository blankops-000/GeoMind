from sqlalchemy import text


def facilities_within_region(db, region_id: int) -> list[dict]:
    query = text("""
        SELECT f.id, f.name, f.feature_type, f.category,
               ST_AsGeoJSON(f.geom) AS geom
        FROM facilities f
        JOIN geographic_regions r ON r.id = :region_id
        WHERE ST_Within(f.geom, r.geom)
    """)
    result = db.execute(query, {"region_id": region_id})
    return [dict(row) for row in result.mappings().all()]


def facilities_within_distance(db, lon: float, lat: float, distance_m: float) -> list[dict]:
    query = text("""
        SELECT f.id, f.name,
               ST_Distance(f.geom::geography,
                           ST_MakePoint(:lon, :lat)::geography) AS distance_m,
               ST_AsGeoJSON(f.geom) AS geom
        FROM facilities f
        WHERE ST_DWithin(f.geom::geography,
                         ST_MakePoint(:lon, :lat)::geography,
                         :distance_m)
        ORDER BY distance_m
    """)
    result = db.execute(query, {"lon": lon, "lat": lat, "distance_m": distance_m})
    return [dict(row) for row in result.mappings().all()]


def region_area_km2(db, region_id: int) -> float:
    query = text("""
        SELECT ST_Area(geom::geography) / 1e6 AS area_km2
        FROM geographic_regions WHERE id = :region_id
    """)
    val = db.execute(query, {"region_id": region_id}).scalar()
    return float(val) if val is not None else 0.0


def count_facilities_by_type(db) -> list[dict]:
    query = text("""
        SELECT feature_type, COUNT(*) AS count
        FROM facilities GROUP BY feature_type
    """)
    result = db.execute(query)
    return [dict(row) for row in result.mappings().all()]
