-- ============================================================
-- GeoMind AI — 03_sample_queries.sql
-- Validated spatial queries for healthcare accessibility
-- Demo area: Nairobi County, Kenya
-- ============================================================

-- ============================================================
-- Q1: Nearest health facility to each analysis region centroid
-- ============================================================
-- Uses CROSS JOIN LATERAL with KNN index (<->) for performance.
-- Returns the single closest operational facility per region.

-- SELECT 
--     r.id AS region_id,
--     r.name AS region_name,
--     h.id AS facility_id,
--     h.name AS facility_name,
--     h.facility_type,
--     ROUND(ST_Distance(
--         ST_Centroid(r.geom)::geography, 
--         h.geom::geography
--     )::numeric, 1) AS distance_meters
-- FROM analysis_regions r
-- CROSS JOIN LATERAL (
--     SELECT id, name, facility_type, geom
--     FROM health_facilities
--     WHERE operational_status = 'Operational'
--       AND geom IS NOT NULL
--     ORDER BY ST_Centroid(r.geom) <-> geom
--     LIMIT 1
-- ) h
-- ORDER BY distance_meters DESC;


-- ============================================================
-- Q2: Population within 5 km of each health facility
-- ============================================================
-- Uses ST_DWithin on geography for accurate distance.

-- SELECT 
--     h.id AS facility_id,
--     h.name AS facility_name,
--     h.facility_type,
--     h.ward,
--     ROUND(SUM(p.population)::numeric, 0) AS population_within_5km,
--     COUNT(p.id) AS grid_cells_covered
-- FROM health_facilities h
-- JOIN population_points p
--     ON ST_DWithin(h.geom::geography, p.geom::geography, 5000)
-- WHERE h.operational_status = 'Operational'
--   AND h.county ILIKE 'Nairobi'
-- GROUP BY h.id, h.name, h.facility_type, h.ward
-- ORDER BY population_within_5km DESC;


-- ============================================================
-- Q3: Wards with NO health facility (healthcare deserts)
-- ============================================================

-- SELECT 
--     ab.name AS ward_name,
--     ab.population AS ward_population,
--     ab.area_sq_km
-- FROM administrative_boundaries ab
-- LEFT JOIN health_facilities hf
--     ON ST_Within(hf.geom, ab.geom)
--     AND hf.operational_status = 'Operational'
-- WHERE ab.level = 'ward'
--   AND hf.id IS NULL
-- ORDER BY ab.population DESC NULLS LAST;


-- ============================================================
-- Q4: Regions where nearest facility is > 10 km away
-- ============================================================

-- SELECT 
--     r.id AS region_id,
--     r.name AS region_name,
--     MIN(ST_Distance(
--         ST_Centroid(r.geom)::geography, 
--         h.geom::geography
--     )) AS min_distance_meters
-- FROM analysis_regions r
-- CROSS JOIN health_facilities h
-- WHERE h.operational_status = 'Operational'
--   AND h.geom IS NOT NULL
-- GROUP BY r.id, r.name
-- HAVING MIN(ST_Distance(
--     ST_Centroid(r.geom)::geography, 
--     h.geom::geography
-- )) > 10000
-- ORDER BY min_distance_meters DESC;


-- ============================================================
-- Q5: Facility density per ward (facilities per sq km)
-- ============================================================

-- SELECT 
--     ab.name AS ward_name,
--     COUNT(hf.id) AS facility_count,
--     ROUND(ab.area_sq_km::numeric, 2) AS area_sq_km,
--     ROUND((COUNT(hf.id) / NULLIF(ab.area_sq_km, 0))::numeric, 3) AS facilities_per_sq_km,
--     ab.population AS ward_population,
--     CASE 
--         WHEN COUNT(hf.id) = 0 THEN 0
--         ELSE ROUND((ab.population / COUNT(hf.id))::numeric, 0)
--     END AS population_per_facility
-- FROM administrative_boundaries ab
-- LEFT JOIN health_facilities hf
--     ON ST_Within(hf.geom, ab.geom)
--     AND hf.operational_status = 'Operational'
-- WHERE ab.level = 'ward'
-- GROUP BY ab.id, ab.name, ab.area_sq_km, ab.population
-- ORDER BY facilities_per_sq_km ASC;


-- ============================================================
-- Q6: Facility type breakdown per sub-county
-- ============================================================

-- SELECT 
--     ab.name AS subcounty_name,
--     hf.facility_type,
--     hf.owner_type,
--     COUNT(*) AS count
-- FROM administrative_boundaries ab
-- JOIN health_facilities hf
--     ON ST_Within(hf.geom, ab.geom)
-- WHERE ab.level = 'subcounty'
--   AND hf.operational_status = 'Operational'
-- GROUP BY ab.name, hf.facility_type, hf.owner_type
-- ORDER BY ab.name, count DESC;


-- ============================================================
-- Q7: Health facilities as GeoJSON FeatureCollection
-- ============================================================
-- Use the built-in function:
-- SELECT fn_facilities_geojson('Nairobi');

-- Or manual query:
-- SELECT jsonb_build_object(
--     'type', 'FeatureCollection',
--     'features', jsonb_agg(
--         jsonb_build_object(
--             'type', 'Feature',
--             'geometry', ST_AsGeoJSON(hf.geom)::jsonb,
--             'properties', jsonb_build_object(
--                 'id', hf.id,
--                 'name', hf.name,
--                 'type', hf.facility_type,
--                 'ownership', hf.owner_type,
--                 'ward', hf.ward,
--                 'keph_level', hf.keph_level
--             )
--         )
--     )
-- )
-- FROM health_facilities hf
-- WHERE hf.county ILIKE 'Nairobi'
--   AND hf.operational_status = 'Operational'
--   AND hf.geom IS NOT NULL;


-- ============================================================
-- Q8: Accessibility results as GeoJSON (for map rendering)
-- ============================================================
-- Use the built-in function:
-- SELECT fn_accessibility_geojson();
-- Or for a specific run:
-- SELECT fn_accessibility_geojson(1);


-- ============================================================
-- Q9: Road network near a facility (500m buffer)
-- ============================================================

-- SELECT 
--     r.osm_id,
--     r.name AS road_name,
--     r.road_class,
--     r.surface,
--     ROUND(ST_Distance(
--         r.geom::geography, 
--         hf.geom::geography
--     )::numeric, 1) AS distance_meters
-- FROM roads r, health_facilities hf
-- WHERE hf.name ILIKE '%Kenyatta National%'
--   AND ST_DWithin(r.geom::geography, hf.geom::geography, 500)
-- ORDER BY distance_meters;


-- ============================================================
-- Q10: Summary statistics for the AI layer
-- ============================================================
-- This query returns aggregate stats that the AI/LLM can use
-- to generate natural-language explanations.

-- SELECT jsonb_build_object(
--     'total_facilities', (SELECT COUNT(*) FROM health_facilities WHERE county ILIKE 'Nairobi' AND operational_status = 'Operational'),
--     'total_hospitals', (SELECT COUNT(*) FROM health_facilities WHERE county ILIKE 'Nairobi' AND facility_type = 'Hospital' AND operational_status = 'Operational'),
--     'total_health_centres', (SELECT COUNT(*) FROM health_facilities WHERE county ILIKE 'Nairobi' AND facility_type = 'Health Centre' AND operational_status = 'Operational'),
--     'total_dispensaries', (SELECT COUNT(*) FROM health_facilities WHERE county ILIKE 'Nairobi' AND facility_type = 'Dispensary' AND operational_status = 'Operational'),
--     'public_facilities', (SELECT COUNT(*) FROM health_facilities WHERE county ILIKE 'Nairobi' AND owner_type = 'Public' AND operational_status = 'Operational'),
--     'private_facilities', (SELECT COUNT(*) FROM health_facilities WHERE county ILIKE 'Nairobi' AND owner_type = 'Private' AND operational_status = 'Operational'),
--     'total_wards', (SELECT COUNT(*) FROM administrative_boundaries WHERE level = 'ward'),
--     'wards_without_facility', (
--         SELECT COUNT(*) FROM administrative_boundaries ab
--         LEFT JOIN health_facilities hf ON ST_Within(hf.geom, ab.geom) AND hf.operational_status = 'Operational'
--         WHERE ab.level = 'ward' AND hf.id IS NULL
--     )
-- ) AS summary_stats;


-- ============================================================
-- NOTES
-- ============================================================
-- Queries are commented out so this file runs without error
-- on empty tables. Uncomment individual queries after loading data.
--
-- Performance tips:
-- - All geometry columns have GiST spatial indexes
-- - Use ::geography cast for accurate meter-based distances
-- - The <-> operator uses the GiST index for KNN searches
-- - ST_DWithin uses the spatial index for radius searches
-- - For very large datasets, consider ST_ClusterDBSCAN for grouping
