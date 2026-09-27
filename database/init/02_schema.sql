-- ============================================================
-- GeoMind AI — 02_schema.sql
-- Full database schema for healthcare accessibility analysis
-- Demo area: Nairobi County, Kenya
-- SRID: 4326 (WGS 84) throughout
-- ============================================================

-- ============================================================
-- 1. ADMINISTRATIVE BOUNDARIES
--    Kenya's 3-tier administrative hierarchy:
--    County → Sub-County → Ward
-- ============================================================

CREATE TABLE IF NOT EXISTS administrative_boundaries (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    level           TEXT NOT NULL CHECK (level IN ('county', 'subcounty', 'ward')),
    code            TEXT UNIQUE,                          -- Official admin code (e.g., "047" for Nairobi)
    parent_id       INTEGER REFERENCES administrative_boundaries(id) ON DELETE SET NULL,
    area_sq_km      NUMERIC,                              -- Computed from geometry
    population      INTEGER,                              -- Census or WorldPop estimate
    geom            GEOMETRY(MultiPolygon, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_admin_geom        ON administrative_boundaries USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_admin_level       ON administrative_boundaries (level);
CREATE INDEX IF NOT EXISTS idx_admin_parent      ON administrative_boundaries (parent_id);
CREATE INDEX IF NOT EXISTS idx_admin_name_trgm   ON administrative_boundaries USING GIN (name gin_trgm_ops);

COMMENT ON TABLE administrative_boundaries IS 'Kenya administrative units: counties, sub-counties, wards. Source: Kenya Open Data / HDX.';


-- ============================================================
-- 2. HEALTH FACILITIES
--    Kenya Master Health Facility Registry (KMHFR) data
-- ============================================================

CREATE TABLE IF NOT EXISTS health_facilities (
    id              SERIAL PRIMARY KEY,
    facility_code   TEXT UNIQUE,                           -- KMHFR facility code
    name            TEXT NOT NULL,
    facility_type   TEXT,                                  -- Hospital, Health Centre, Dispensary, Clinic, etc.
    keph_level      TEXT,                                  -- KEPH Level (1–6)
    ownership       TEXT,                                  -- Ministry of Health, Private, Faith Based, NGO, etc.
    owner_type      TEXT,                                  -- Public, Private, Faith Based
    operational_status TEXT DEFAULT 'Operational',         -- Operational, Non-Operational, Closed
    county          TEXT,
    subcounty       TEXT,
    ward            TEXT,
    constituency    TEXT,
    latitude        NUMERIC,                               -- Original lat from source
    longitude       NUMERIC,                               -- Original lon from source
    services        JSONB DEFAULT '[]'::jsonb,             -- Array of service names
    contacts        JSONB DEFAULT '{}'::jsonb,             -- Phone, email, etc.
    beds            INTEGER,
    cots            INTEGER,
    source          TEXT DEFAULT 'KMHFR',
    date_acquired   DATE,
    geom            GEOMETRY(Point, 4326)                  -- Built from lat/lon
);

CREATE INDEX IF NOT EXISTS idx_hf_geom           ON health_facilities USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_hf_type           ON health_facilities (facility_type);
CREATE INDEX IF NOT EXISTS idx_hf_ownership      ON health_facilities (owner_type);
CREATE INDEX IF NOT EXISTS idx_hf_keph           ON health_facilities (keph_level);
CREATE INDEX IF NOT EXISTS idx_hf_status         ON health_facilities (operational_status);
CREATE INDEX IF NOT EXISTS idx_hf_county         ON health_facilities (county);
CREATE INDEX IF NOT EXISTS idx_hf_subcounty      ON health_facilities (subcounty);
CREATE INDEX IF NOT EXISTS idx_hf_ward           ON health_facilities (ward);
CREATE INDEX IF NOT EXISTS idx_hf_name_trgm      ON health_facilities USING GIN (name gin_trgm_ops);

COMMENT ON TABLE health_facilities IS 'Health facilities in Nairobi County. Source: Kenya Master Health Facility Registry (KMHFR).';


-- ============================================================
-- 3. ROADS / TRANSPORT NETWORK
--    OpenStreetMap road network via Overpass API
-- ============================================================

CREATE TABLE IF NOT EXISTS roads (
    id              SERIAL PRIMARY KEY,
    osm_id          BIGINT UNIQUE,
    name            TEXT,
    road_class      TEXT,                                  -- motorway, trunk, primary, secondary, tertiary, residential, etc.
    surface         TEXT,                                  -- paved, unpaved, gravel, earth, etc.
    lanes           INTEGER,
    oneway          BOOLEAN DEFAULT FALSE,
    length_meters   NUMERIC,                               -- Computed from geometry (geography cast)
    geom            GEOMETRY(LineString, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_roads_geom        ON roads USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_roads_class       ON roads (road_class);
CREATE INDEX IF NOT EXISTS idx_roads_surface     ON roads (surface);

COMMENT ON TABLE roads IS 'Road network for Nairobi County. Source: OpenStreetMap via Overpass API.';


-- ============================================================
-- 4. POPULATION POINTS / GRID
--    WorldPop aggregated population estimates
--    Each row = one grid cell with estimated population
-- ============================================================

CREATE TABLE IF NOT EXISTS population_points (
    id              SERIAL PRIMARY KEY,
    grid_id         TEXT UNIQUE,                           -- e.g., "nairobi_100m_r042_c117"
    population      NUMERIC NOT NULL DEFAULT 0,            -- Estimated people in this cell
    resolution_m    INTEGER DEFAULT 100,                   -- Grid resolution in meters
    source          TEXT DEFAULT 'WorldPop',
    year            INTEGER,
    geom            GEOMETRY(Point, 4326) NOT NULL         -- Centroid of grid cell
);

CREATE INDEX IF NOT EXISTS idx_pop_geom          ON population_points USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_pop_population    ON population_points (population);

COMMENT ON TABLE population_points IS 'Population grid centroids (WorldPop Kenya). Each point represents estimated population in a grid cell.';


-- ============================================================
-- 5. SETTLEMENTS / BUILDINGS (Optional contextual layer)
--    OSM buildings or named places
-- ============================================================

CREATE TABLE IF NOT EXISTS settlements (
    id              SERIAL PRIMARY KEY,
    osm_id          BIGINT,
    name            TEXT,
    settlement_type TEXT,                                  -- residential, commercial, estate, slum, village
    population      INTEGER,                               -- If known
    geom            GEOMETRY(Point, 4326)
);

CREATE INDEX IF NOT EXISTS idx_settlements_geom  ON settlements USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_settlements_type  ON settlements (settlement_type);

COMMENT ON TABLE settlements IS 'Named settlements and places. Source: OpenStreetMap.';


-- ============================================================
-- 6. ANALYSIS REGIONS
--    Grid cells or ward-level polygons used as analysis units.
--    Each region gets an accessibility score.
-- ============================================================

CREATE TABLE IF NOT EXISTS analysis_regions (
    id              SERIAL PRIMARY KEY,
    name            TEXT,
    region_type     TEXT CHECK (region_type IN ('ward', 'grid_cell', 'custom')),
    admin_id        INTEGER REFERENCES administrative_boundaries(id) ON DELETE SET NULL,
    area_sq_km      NUMERIC,
    centroid        GEOMETRY(Point, 4326),                 -- Pre-computed centroid
    geom            GEOMETRY(MultiPolygon, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ar_geom           ON analysis_regions USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_ar_type           ON analysis_regions (region_type);

COMMENT ON TABLE analysis_regions IS 'Analysis units (wards or grid cells) for accessibility scoring.';


-- ============================================================
-- 7. ANALYSIS RUNS
--    Tracks each analysis execution for reproducibility.
--    Must be created BEFORE accessibility_results (FK dependency).
-- ============================================================

CREATE TABLE IF NOT EXISTS analysis_runs (
    id              SERIAL PRIMARY KEY,
    query           TEXT,                                  -- Natural language query that triggered this
    run_type        TEXT DEFAULT 'accessibility',           -- accessibility, coverage, equity, etc.
    demo_area       TEXT DEFAULT 'Nairobi County',
    parameters      JSONB DEFAULT '{}'::jsonb,             -- Distance thresholds, weights, filters
    result_summary  JSONB DEFAULT '{}'::jsonb,             -- Aggregate stats for the run
    status          TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    created_by      TEXT DEFAULT 'system'
);

COMMENT ON TABLE analysis_runs IS 'Tracks each analysis execution with parameters and summary results.';


-- ============================================================
-- 8. ACCESSIBILITY RESULTS
--    Core output table: one row per region per analysis run.
--    This is what drives the map visualization.
-- ============================================================

CREATE TABLE IF NOT EXISTS accessibility_results (
    id                      SERIAL PRIMARY KEY,
    run_id                  INTEGER REFERENCES analysis_runs(id) ON DELETE CASCADE,
    region_id               INTEGER REFERENCES analysis_regions(id) ON DELETE CASCADE,
    nearest_facility_id     INTEGER REFERENCES health_facilities(id) ON DELETE SET NULL,
    nearest_facility_name   TEXT,
    distance_meters         NUMERIC,                       -- Straight-line distance to nearest facility
    travel_time_minutes     NUMERIC,                       -- Estimated travel time (if road network used)
    facility_count_5km      INTEGER DEFAULT 0,             -- Facilities within 5 km
    facility_count_10km     INTEGER DEFAULT 0,             -- Facilities within 10 km
    population_covered      NUMERIC DEFAULT 0,             -- Population in this region
    population_within_5km   NUMERIC DEFAULT 0,             -- Pop within 5 km of any facility
    accessibility_score     NUMERIC,                       -- 0–100 composite score
    accessibility_category  TEXT CHECK (accessibility_category IN (
                                'excellent', 'good', 'moderate', 'limited', 'critical'
                            )),
    factors                 JSONB DEFAULT '{}'::jsonb,     -- Contributing factors breakdown
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE (run_id, region_id)
);

CREATE INDEX IF NOT EXISTS idx_ar_results_run    ON accessibility_results (run_id);
CREATE INDEX IF NOT EXISTS idx_ar_results_cat    ON accessibility_results (accessibility_category);
CREATE INDEX IF NOT EXISTS idx_ar_results_score  ON accessibility_results (accessibility_score);

COMMENT ON TABLE accessibility_results IS 'Healthcare accessibility scores per region per analysis run.';


-- ============================================================
-- 9. SPATIAL FINDINGS / AI EVIDENCE
--    Geographic evidence that the AI layer can reference.
--    Each finding is tied to a region and has a geometry.
-- ============================================================

CREATE TABLE IF NOT EXISTS spatial_findings (
    id              SERIAL PRIMARY KEY,
    run_id          INTEGER REFERENCES analysis_runs(id) ON DELETE CASCADE,
    region_id       INTEGER REFERENCES analysis_regions(id) ON DELETE SET NULL,
    finding_type    TEXT NOT NULL,                          -- gap, cluster, desert, underserved, etc.
    severity        TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title           TEXT,
    description     TEXT,
    evidence        JSONB DEFAULT '{}'::jsonb,             -- Supporting data/stats
    recommendations JSONB DEFAULT '[]'::jsonb,             -- AI-generated suggestions
    geom            GEOMETRY(Geometry, 4326),               -- Point, line, or polygon
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_findings_geom     ON spatial_findings USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_findings_type     ON spatial_findings (finding_type);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON spatial_findings (severity);
CREATE INDEX IF NOT EXISTS idx_findings_run      ON spatial_findings (run_id);

COMMENT ON TABLE spatial_findings IS 'AI-generated spatial findings and evidence for map display and explanations.';


-- ============================================================
-- 10. SATELLITE IMAGERY METADATA (reference only)
--     Actual imagery stored on disk, not in PostGIS.
-- ============================================================

CREATE TABLE IF NOT EXISTS satellite_imagery (
    id              SERIAL PRIMARY KEY,
    scene_id        TEXT UNIQUE,
    satellite       TEXT DEFAULT 'Sentinel-2',
    acquisition_date DATE,
    cloud_cover_pct NUMERIC,
    resolution_m    NUMERIC,
    bands           TEXT[],                                -- e.g., {'B02','B03','B04','B08'}
    file_path       TEXT,                                  -- Local path to imagery file
    bbox            GEOMETRY(Polygon, 4326),               -- Bounding box of the scene
    metadata        JSONB DEFAULT '{}'::jsonb,
    processed       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sat_bbox          ON satellite_imagery USING GIST (bbox);
CREATE INDEX IF NOT EXISTS idx_sat_date          ON satellite_imagery (acquisition_date);

COMMENT ON TABLE satellite_imagery IS 'Metadata for Sentinel-2 scenes. Actual rasters stored on filesystem.';


-- ============================================================
-- 11. QUERY LOG
--     Tracks natural-language queries from users
-- ============================================================

CREATE TABLE IF NOT EXISTS query_log (
    id              SERIAL PRIMARY KEY,
    session_id      UUID DEFAULT uuid_generate_v4(),
    query_text      TEXT NOT NULL,
    intent          TEXT,                                   -- Classified intent
    parameters      JSONB DEFAULT '{}'::jsonb,
    response        JSONB DEFAULT '{}'::jsonb,
    run_id          INTEGER REFERENCES analysis_runs(id) ON DELETE SET NULL,
    latency_ms      INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ql_session        ON query_log (session_id);
CREATE INDEX IF NOT EXISTS idx_ql_created        ON query_log (created_at);

COMMENT ON TABLE query_log IS 'Audit log of natural-language queries processed by the AI interface.';


-- ============================================================
-- 12. HELPER VIEWS
-- ============================================================

-- View: Facility summary per ward
CREATE OR REPLACE VIEW v_facility_count_by_ward AS
SELECT 
    ab.name AS ward_name,
    ab.code AS ward_code,
    COUNT(hf.id) AS facility_count,
    COUNT(CASE WHEN hf.owner_type = 'Public' THEN 1 END) AS public_count,
    COUNT(CASE WHEN hf.owner_type = 'Private' THEN 1 END) AS private_count,
    COUNT(CASE WHEN hf.facility_type = 'Hospital' THEN 1 END) AS hospital_count,
    COUNT(CASE WHEN hf.facility_type = 'Health Centre' THEN 1 END) AS health_centre_count,
    COUNT(CASE WHEN hf.facility_type = 'Dispensary' THEN 1 END) AS dispensary_count,
    ab.population AS ward_population,
    ab.geom
FROM administrative_boundaries ab
LEFT JOIN health_facilities hf
    ON ST_Within(hf.geom, ab.geom) AND hf.operational_status = 'Operational'
WHERE ab.level = 'ward'
GROUP BY ab.id, ab.name, ab.code, ab.population, ab.geom;

COMMENT ON VIEW v_facility_count_by_ward IS 'Facility counts and types per ward for quick overview.';


-- View: Accessibility results with geometry (for GeoJSON export)
CREATE OR REPLACE VIEW v_accessibility_geojson AS
SELECT 
    ar.id AS result_id,
    reg.name AS region_name,
    reg.region_type,
    ar.nearest_facility_name,
    ar.distance_meters,
    ar.travel_time_minutes,
    ar.facility_count_5km,
    ar.facility_count_10km,
    ar.population_covered,
    ar.accessibility_score,
    ar.accessibility_category,
    ar.factors,
    reg.geom
FROM accessibility_results ar
JOIN analysis_regions reg ON ar.region_id = reg.id;

COMMENT ON VIEW v_accessibility_geojson IS 'Join of accessibility results with region geometries for GeoJSON output.';


-- ============================================================
-- 13. FUNCTIONS
-- ============================================================

-- Function: Build GeoJSON FeatureCollection from accessibility results
CREATE OR REPLACE FUNCTION fn_accessibility_geojson(p_run_id INTEGER DEFAULT NULL)
RETURNS JSONB AS $$
BEGIN
    RETURN (
        SELECT jsonb_build_object(
            'type', 'FeatureCollection',
            'metadata', jsonb_build_object(
                'generated_at', NOW(),
                'demo_area', 'Nairobi County',
                'run_id', p_run_id
            ),
            'features', COALESCE(jsonb_agg(
                jsonb_build_object(
                    'type', 'Feature',
                    'geometry', ST_AsGeoJSON(v.geom)::jsonb,
                    'properties', jsonb_build_object(
                        'id', v.result_id,
                        'name', v.region_name,
                        'type', v.region_type,
                        'nearest_facility', v.nearest_facility_name,
                        'distance_meters', ROUND(v.distance_meters::numeric, 1),
                        'travel_time_minutes', v.travel_time_minutes,
                        'facilities_within_5km', v.facility_count_5km,
                        'facilities_within_10km', v.facility_count_10km,
                        'population', v.population_covered,
                        'score', v.accessibility_score,
                        'category', v.accessibility_category,
                        'factors', v.factors
                    )
                )
            ), '[]'::jsonb)
        )
        FROM v_accessibility_geojson v
        WHERE p_run_id IS NULL OR v.result_id IN (
            SELECT ar2.id FROM accessibility_results ar2 WHERE ar2.run_id = p_run_id
        )
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION fn_accessibility_geojson IS 'Returns accessibility results as a GeoJSON FeatureCollection.';


-- Function: Build GeoJSON for health facilities
CREATE OR REPLACE FUNCTION fn_facilities_geojson(
    p_county TEXT DEFAULT 'Nairobi',
    p_facility_type TEXT DEFAULT NULL
)
RETURNS JSONB AS $$
BEGIN
    RETURN (
        SELECT jsonb_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(jsonb_agg(
                jsonb_build_object(
                    'type', 'Feature',
                    'geometry', ST_AsGeoJSON(hf.geom)::jsonb,
                    'properties', jsonb_build_object(
                        'id', hf.id,
                        'code', hf.facility_code,
                        'name', hf.name,
                        'type', hf.facility_type,
                        'keph_level', hf.keph_level,
                        'ownership', hf.ownership,
                        'owner_type', hf.owner_type,
                        'status', hf.operational_status,
                        'subcounty', hf.subcounty,
                        'ward', hf.ward,
                        'beds', hf.beds,
                        'services', hf.services
                    )
                )
            ), '[]'::jsonb)
        )
        FROM health_facilities hf
        WHERE hf.county ILIKE p_county
          AND hf.operational_status = 'Operational'
          AND hf.geom IS NOT NULL
          AND (p_facility_type IS NULL OR hf.facility_type ILIKE p_facility_type)
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION fn_facilities_geojson IS 'Returns health facilities as a GeoJSON FeatureCollection, filtered by county and optional type.';


-- Function: Compute basic accessibility stats for a region
CREATE OR REPLACE FUNCTION fn_region_accessibility(p_region_geom GEOMETRY)
RETURNS TABLE (
    nearest_facility_id     INTEGER,
    nearest_facility_name   TEXT,
    nearest_facility_type   TEXT,
    distance_meters         NUMERIC,
    facility_count_5km      BIGINT,
    facility_count_10km     BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH nearest AS (
        SELECT 
            hf.id,
            hf.name,
            hf.facility_type,
            ST_Distance(ST_Centroid(p_region_geom)::geography, hf.geom::geography) AS dist_m
        FROM health_facilities hf
        WHERE hf.operational_status = 'Operational'
          AND hf.geom IS NOT NULL
        ORDER BY ST_Centroid(p_region_geom) <-> hf.geom
        LIMIT 1
    )
    SELECT 
        n.id,
        n.name,
        n.facility_type,
        ROUND(n.dist_m::numeric, 1),
        (SELECT COUNT(*) FROM health_facilities hf2 
         WHERE hf2.operational_status = 'Operational' 
           AND hf2.geom IS NOT NULL
           AND ST_DWithin(ST_Centroid(p_region_geom)::geography, hf2.geom::geography, 5000)),
        (SELECT COUNT(*) FROM health_facilities hf3 
         WHERE hf3.operational_status = 'Operational' 
           AND hf3.geom IS NOT NULL
           AND ST_DWithin(ST_Centroid(p_region_geom)::geography, hf3.geom::geography, 10000))
    FROM nearest n;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION fn_region_accessibility IS 'For a given geometry, returns nearest facility and facility counts at 5km/10km radii.';
