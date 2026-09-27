# GeoMind AI — Database Schema Documentation

> **Database:** PostgreSQL 16 + PostGIS 3.4  
> **SRID:** 4326 (WGS 84) throughout  
> **Demo Area:** Nairobi County, Kenya

---

## Entity Relationship Diagram

```mermaid
erDiagram
    administrative_boundaries ||--o{ administrative_boundaries : "parent_id"
    administrative_boundaries ||--o{ analysis_regions : "admin_id"
    analysis_regions ||--o{ accessibility_results : "region_id"
    analysis_runs ||--o{ accessibility_results : "run_id"
    health_facilities ||--o{ accessibility_results : "nearest_facility_id"
    analysis_runs ||--o{ spatial_findings : "run_id"
    analysis_regions ||--o{ spatial_findings : "region_id"
    analysis_runs ||--o{ query_log : "run_id"

    administrative_boundaries {
        serial id PK
        text name
        text level "county|subcounty|ward"
        text code UK
        integer parent_id FK
        numeric area_sq_km
        integer population
        geometry geom "MultiPolygon 4326"
    }

    health_facilities {
        serial id PK
        text facility_code UK
        text name
        text facility_type
        text keph_level
        text ownership
        text owner_type
        text operational_status
        text county
        text subcounty
        text ward
        numeric latitude
        numeric longitude
        jsonb services
        integer beds
        geometry geom "Point 4326"
    }

    roads {
        serial id PK
        bigint osm_id UK
        text name
        text road_class
        text surface
        integer lanes
        boolean oneway
        numeric length_meters
        geometry geom "LineString 4326"
    }

    population_points {
        serial id PK
        text grid_id UK
        numeric population
        integer resolution_m
        geometry geom "Point 4326"
    }

    analysis_regions {
        serial id PK
        text name
        text region_type "ward|grid_cell|custom"
        integer admin_id FK
        numeric area_sq_km
        geometry geom "MultiPolygon 4326"
    }

    analysis_runs {
        serial id PK
        text query
        text run_type
        text demo_area
        jsonb parameters
        jsonb result_summary
        text status
        timestamptz started_at
    }

    accessibility_results {
        serial id PK
        integer run_id FK
        integer region_id FK
        integer nearest_facility_id FK
        numeric distance_meters
        numeric travel_time_minutes
        integer facility_count_5km
        numeric accessibility_score
        text accessibility_category
        jsonb factors
    }

    spatial_findings {
        serial id PK
        integer run_id FK
        integer region_id FK
        text finding_type
        text severity
        text description
        jsonb evidence
        geometry geom "Geometry 4326"
    }
```

---

## Tables Summary

| # | Table | Purpose | Geometry | Records (est.) |
|---|---|---|---|---|
| 1 | `administrative_boundaries` | County/subcounty/ward polygons | MultiPolygon | ~100 |
| 2 | `health_facilities` | KMHFR facility locations | Point | ~1,000–1,500 |
| 3 | `roads` | OSM road network | LineString | ~50,000–100,000 |
| 4 | `population_points` | WorldPop grid centroids | Point | ~10,000+ |
| 5 | `settlements` | Named places (optional) | Point | varies |
| 6 | `analysis_regions` | Analysis units (wards/grid) | MultiPolygon | ~85 |
| 7 | `analysis_runs` | Analysis execution tracking | — | per-query |
| 8 | `accessibility_results` | Scores per region per run | — | ~85/run |
| 9 | `spatial_findings` | AI evidence/insights | Geometry | varies |
| 10 | `satellite_imagery` | Sentinel-2 metadata | Polygon (bbox) | ~5–10 |
| 11 | `query_log` | NL query audit trail | — | per-query |

---

## Views

| View | Purpose |
|---|---|
| `v_facility_count_by_ward` | Facility counts/types per ward with population |
| `v_accessibility_geojson` | Accessibility results joined with region geometries |

## Functions

| Function | Returns | Purpose |
|---|---|---|
| `fn_accessibility_geojson(run_id)` | JSONB | Full GeoJSON FeatureCollection of accessibility results |
| `fn_facilities_geojson(county, type)` | JSONB | GeoJSON FeatureCollection of health facilities |
| `fn_region_accessibility(geom)` | TABLE | Nearest facility + counts for any input geometry |

---

## Spatial Indexes

All geometry columns have GiST spatial indexes. Key indexes:

| Index | Table | Column | Type |
|---|---|---|---|
| `idx_admin_geom` | administrative_boundaries | geom | GIST |
| `idx_hf_geom` | health_facilities | geom | GIST |
| `idx_roads_geom` | roads | geom | GIST |
| `idx_pop_geom` | population_points | geom | GIST |
| `idx_ar_geom` | analysis_regions | geom | GIST |
| `idx_findings_geom` | spatial_findings | geom | GIST |
| `idx_sat_bbox` | satellite_imagery | bbox | GIST |

Additional attribute indexes on frequently filtered columns (facility_type, road_class, level, etc.) — see [02_schema.sql](file:///c:/Users/mutwi/OneDrive/Documents/GeoMind-database/database/init/02_schema.sql) for full list.

---

## Accessibility Category Scale

| Category | Score | Distance to Nearest Facility |
|---|---|---|
| `excellent` | 80–100 | < 1 km |
| `good` | 60–79 | 1–3 km |
| `moderate` | 40–59 | 3–5 km |
| `limited` | 20–39 | 5–10 km |
| `critical` | 0–19 | > 10 km |
