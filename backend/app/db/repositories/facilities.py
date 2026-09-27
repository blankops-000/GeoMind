from app.db.spatial_queries import (
    facilities_within_region,
    facilities_within_distance,
    count_facilities_by_type,
)


class FacilityRepository:
    def __init__(self, db):
        self.db = db

    def within_region(self, region_id: int) -> list[dict]:
        return facilities_within_region(self.db, region_id)

    def within_distance(self, lon: float, lat: float, distance_m: float) -> list[dict]:
        return facilities_within_distance(self.db, lon, lat, distance_m)

    def count_by_type(self) -> list[dict]:
        return count_facilities_by_type(self.db)
