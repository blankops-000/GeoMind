"""Spatial statistical computation functions using PostGIS."""

from typing import Dict
from sqlalchemy import text
from sqlalchemy.orm import Session


def region_area_km2(db: Session, region_id: int) -> float:
    """Calculate the area of a region in square kilometers."""
    try:
        query = text("""
            SELECT ST_Area(geom::geography) / 1e6 AS area_km2
            FROM geographic_regions
            WHERE id = :region_id
        """)
        val = db.execute(query, {"region_id": region_id}).scalar()
        return float(val) if val is not None else 0.0
    except Exception:
        return 0.0


def facility_count(db: Session) -> int:
    """Count the total number of facilities."""
    try:
        query = text("SELECT COUNT(*) FROM facilities")
        val = db.execute(query).scalar()
        return int(val) if val is not None else 0
    except Exception:
        return 0


def facilities_by_type(db: Session) -> Dict[str, int]:
    """Get count of facilities grouped by feature_type."""
    try:
        query = text("""
            SELECT feature_type, COUNT(*) AS count
            FROM facilities
            GROUP BY feature_type
        """)
        result = db.execute(query)
        return {row.feature_type: int(row.count) for row in result.mappings().all()}
    except Exception:
        return {}


def facilities_in_region_count(db: Session, region_id: int) -> int:
    """Count facilities located within a specific region."""
    try:
        query = text("""
            SELECT COUNT(f.id) AS count
            FROM facilities f
            JOIN geographic_regions r ON r.id = :region_id
            WHERE ST_Within(f.geom, r.geom)
        """)
        val = db.execute(query, {"region_id": region_id}).scalar()
        return int(val) if val is not None else 0
    except Exception:
        return 0


def avg_facility_distance_to_point(db: Session, lon: float, lat: float) -> float:
    """Calculate average distance (in meters) from all facilities to a point."""
    try:
        query = text("""
            SELECT AVG(ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography)) AS avg_dist
            FROM facilities
        """)
        val = db.execute(query, {"lon": lon, "lat": lat}).scalar()
        return float(val) if val is not None else 0.0
    except Exception:
        return 0.0


def density_per_km2(feature_count: int, area_km2: float) -> float:
    """Calculate feature density per square kilometer."""
    if area_km2 <= 0:
        return 0.0
    return float(feature_count / area_km2)
