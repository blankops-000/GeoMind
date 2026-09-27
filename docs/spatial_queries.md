# GeoMind AI — PostGIS Spatial Queries & Analysis Guide

> **Core PostGIS Engine Reference for GeoMind Hackathon MVP**  
> Demo Area: **Nairobi County, Kenya** (SRID: EPSG:4326)

---

## 1. Spatial Indexing Architecture

PostGIS utilizes **Generalized Search Tree (GiST)** indexing on geometry columns, with R-Tree mechanics for bounding box spatial queries.

### Key Indexing Rules:
1. **Always Index `geom`:**
   ```sql
   CREATE INDEX idx_health_geom ON health_facilities USING GIST (geom);
   CREATE INDEX idx_admin_geom ON administrative_boundaries USING GIST (geom);
   CREATE INDEX idx_roads_geom ON roads USING GIST (geom);
   ```
2. **K-Nearest Neighbors (KNN) Operator (`<->`):**
   * The `<->` operator computes bounding box or point-to-point distance using the GiST index directly, avoiding full sequential scans.
   * Crucial for finding the nearest facility to a point in milliseconds.
3. **Geography vs. Geometry Casting:**
   * EPSG:4326 geometry uses degree units. 1 degree at the equator is ~111.32 km.
   * For accurate metric distances (e.g. within 5 km or distance in meters), we cast to `geography`:
     ```sql
     ST_Distance(geom1::geography, geom2::geography)
     ST_DWithin(geom1::geography, geom2::geography, 5000) -- 5000 meters
     ```

---

## 2. Core Operational Spatial Queries

### Query 1: Nearest Health Facility per Ward (KNN Lateral Join)
Calculates the closest operational health facility to each ward's population centroid.
```sql
SELECT 
    ab.id AS ward_id,
    ab.name AS ward_name,
    hf.id AS facility_id,
    hf.name AS facility_name,
    hf.facility_type,
    ROUND(ST_Distance(ST_Centroid(ab.geom)::geography, hf.geom::geography)::numeric, 1) AS distance_meters
FROM administrative_boundaries ab
CROSS JOIN LATERAL (
    SELECT id, name, facility_type, geom
    FROM health_facilities
    WHERE operational_status = 'Operational'
      AND geom IS NOT NULL
    ORDER BY ST_Centroid(ab.geom) <-> geom
    LIMIT 1
) hf
WHERE ab.level = 'ward'
ORDER BY distance_meters DESC;
```

---

### Query 2: Catchment Analysis (Population within 5 km Radius)
Aggregates population grid points that fall within a 5 km buffer of major facilities.
```sql
SELECT 
    hf.id,
    hf.name,
    hf.facility_type,
    hf.ward,
    ROUND(SUM(p.population)::numeric, 0) AS population_served_5km,
    COUNT(p.id) AS active_grid_points
FROM health_facilities hf
JOIN population_points p
  ON ST_DWithin(hf.geom::geography, p.geom::geography, 5000)
WHERE hf.county ILIKE 'Nairobi'
  AND hf.operational_status = 'Operational'
GROUP BY hf.id, hf.name, hf.facility_type, hf.ward
ORDER BY population_served_5km DESC;
```

---

### Query 3: Identifying Healthcare Deserts
Wards with zero operational health facilities located within their administrative boundaries:
```sql
SELECT 
    ab.id,
    ab.name AS ward_name,
    ab.population,
    ROUND(ab.area_sq_km::numeric, 2) AS area_sq_km
FROM administrative_boundaries ab
LEFT JOIN health_facilities hf
  ON ST_Within(hf.geom, ab.geom)
  AND hf.operational_status = 'Operational'
WHERE ab.level = 'ward'
  AND hf.id IS NULL
ORDER BY ab.population DESC NULLS LAST;
```

---

### Query 4: Road Accessibility & Transit Buffer
Extracts primary and secondary road segments within 1 km of any Level 4, 5, or 6 hospital to assess emergency vehicle access:
```sql
SELECT 
    r.osm_id,
    r.name AS road_name,
    r.road_class,
    r.surface,
    hf.name AS facility_name,
    ROUND(ST_Distance(r.geom::geography, hf.geom::geography)::numeric, 1) AS distance_meters
FROM roads r
JOIN health_facilities hf
  ON ST_DWithin(r.geom::geography, hf.geom::geography, 1000)
WHERE hf.keph_level IN ('Level 4', 'Level 5', 'Level 6')
  AND r.road_class IN ('primary', 'secondary', 'trunk', 'motorway')
ORDER BY distance_meters ASC;
```

---

### Query 5: Full GeoJSON FeatureCollection Generation for Frontend
Executes directly inside PostgreSQL in a single database round-trip:
```sql
SELECT fn_accessibility_geojson();
```
Or for facility markers:
```sql
SELECT fn_facilities_geojson('Nairobi', 'Hospital');
```

---

## 3. Query Performance & EXPLAIN ANALYZE

To verify index usage, run:
```sql
EXPLAIN ANALYZE
SELECT id, name
FROM health_facilities
WHERE ST_DWithin(geom::geography, ST_MakePoint(36.8219, -1.2921)::geography, 3000);
```
**Expected Plan:** `Bitmap Index Scan on idx_health_geom` or `Index Scan`. If you see `Seq Scan` on a populated table, ensure the table has been analyzed (`ANALYZE health_facilities;`).
