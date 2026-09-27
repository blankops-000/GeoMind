from sqlalchemy import text
from app.db.models import GeographicRegion


class RegionRepository:
    def __init__(self, db):
        self.db = db

    def get_by_id(self, region_id: int) -> dict | None:
        query = text("""
            SELECT id, name, region_type, parent_id,
                   ST_AsGeoJSON(geom) AS geom, attributes
            FROM geographic_regions
            WHERE id = :region_id
        """)
        row = self.db.execute(query, {"region_id": region_id}).mappings().first()
        return dict(row) if row else None

    def list_all(self) -> list[dict]:
        query = text("""
            SELECT id, name, region_type, parent_id,
                   ST_AsGeoJSON(geom) AS geom, attributes
            FROM geographic_regions
        """)
        rows = self.db.execute(query).mappings().all()
        return [dict(row) for row in rows]

    def find_containing(self, lon: float, lat: float) -> dict | None:
        query = text("""
            SELECT id, name, region_type, parent_id,
                   ST_AsGeoJSON(geom) AS geom, attributes
            FROM geographic_regions
            WHERE ST_Contains(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
            LIMIT 1
        """)
        row = self.db.execute(query, {"lon": lon, "lat": lat}).mappings().first()
        return dict(row) if row else None
