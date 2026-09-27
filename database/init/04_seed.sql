-- ============================================================
-- GeoMind AI — 04_seed.sql
-- Seed sample Nairobi data for instant local testing
-- Auto-executed on first container boot
-- ============================================================

-- 1. Administrative Boundaries (County, Sub-counties, Wards)
INSERT INTO administrative_boundaries (name, level, code, area_sq_km, population, geom)
VALUES 
(
    'Nairobi', 'county', 'KE047', 696.0, 4397073,
    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[36.65,-1.45],[37.10,-1.45],[37.10,-1.15],[36.65,-1.15],[36.65,-1.45]]]}'), 4326))
)
ON CONFLICT (code) DO NOTHING;

-- Sub-counties
INSERT INTO administrative_boundaries (name, level, code, area_sq_km, population, parent_id, geom)
VALUES
(
    'Kibra', 'subcounty', 'KE047_KIB', 12.1, 185777,
    (SELECT id FROM administrative_boundaries WHERE code = 'KE047'),
    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[36.77,-1.33],[36.83,-1.33],[36.83,-1.29],[36.77,-1.29],[36.77,-1.33]]]}'), 4326))
),
(
    'Embakasi South', 'subcounty', 'KE047_EMS', 27.5, 273838,
    (SELECT id FROM administrative_boundaries WHERE code = 'KE047'),
    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[36.85,-1.35],[36.92,-1.35],[36.92,-1.30],[36.85,-1.30],[36.85,-1.35]]]}'), 4326))
),
(
    'Kasarani', 'subcounty', 'KE047_KAS', 152.6, 780656,
    (SELECT id FROM administrative_boundaries WHERE code = 'KE047'),
    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[36.90,-1.28],[37.05,-1.28],[37.05,-1.18],[36.90,-1.18],[36.90,-1.28]]]}'), 4326))
)
ON CONFLICT (code) DO NOTHING;

-- Wards
INSERT INTO administrative_boundaries (name, level, code, area_sq_km, population, parent_id, geom)
VALUES
(
    'Kenyatta Golf Course', 'ward', 'KE047_W01', 3.8, 38400,
    (SELECT id FROM administrative_boundaries WHERE code = 'KE047_KIB'),
    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[36.800,-1.310],[36.820,-1.310],[36.820,-1.295],[36.800,-1.295],[36.800,-1.310]]]}'), 4326))
),
(
    'Makina', 'ward', 'KE047_W02', 2.1, 72500,
    (SELECT id FROM administrative_boundaries WHERE code = 'KE047_KIB'),
    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[36.775,-1.325],[36.795,-1.325],[36.795,-1.305],[36.775,-1.305],[36.775,-1.325]]]}'), 4326))
),
(
    'Kwa Njenga', 'ward', 'KE047_W03', 4.5, 84100,
    (SELECT id FROM administrative_boundaries WHERE code = 'KE047_EMS'),
    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[36.870,-1.345],[36.895,-1.345],[36.895,-1.320],[36.870,-1.320],[36.870,-1.345]]]}'), 4326))
),
(
    'Ruai', 'ward', 'KE047_W04', 98.2, 46200,
    (SELECT id FROM administrative_boundaries WHERE code = 'KE047_KAS'),
    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[36.950,-1.290],[37.000,-1.290],[37.000,-1.250],[36.950,-1.250],[36.950,-1.290]]]}'), 4326))
)
ON CONFLICT (code) DO NOTHING;


-- 2. Health Facilities (Nairobi Sample)
INSERT INTO health_facilities (
    facility_code, name, facility_type, keph_level, ownership, owner_type, 
    operational_status, county, subcounty, ward, latitude, longitude, beds, cots, services, geom
) VALUES
(
    '13023', 'Kenyatta National Hospital', 'National Referral Hospital', 'Level 6',
    'Ministry of Health', 'Public', 'Operational', 'Nairobi', 'Kibra', 'Kenyatta Golf Course',
    -1.3015, 36.8078, 1800, 120, '["Emergency", "ICU", "Maternity", "Surgery", "Oncology"]'::jsonb,
    ST_SetSRID(ST_MakePoint(36.8078, -1.3015), 4326)
),
(
    '13088', 'The Nairobi Hospital', 'Tertiary Referral Hospital', 'Level 6',
    'Private Practice', 'Private', 'Operational', 'Nairobi', 'Dagoretti North', 'Kilimani',
    -1.2721, 36.8145, 355, 30, '["Emergency", "Trauma", "Cardiology", "Surgery"]'::jsonb,
    ST_SetSRID(ST_MakePoint(36.8145, -1.2721), 4326)
),
(
    '13045', 'Mbagathi County Hospital', 'County Referral Hospital', 'Level 5',
    'County Government of Nairobi', 'Public', 'Operational', 'Nairobi', 'Langata', 'Nairobi West',
    -1.3120, 36.8091, 280, 20, '["Infectious Diseases", "Inpatient", "Maternity"]'::jsonb,
    ST_SetSRID(ST_MakePoint(36.8091, -1.3120), 4326)
),
(
    '13110', 'Pumwani Maternity Hospital', 'Specialized Hospital', 'Level 5',
    'County Government of Nairobi', 'Public', 'Operational', 'Nairobi', 'Kamukunji', 'Pumwani',
    -1.2825, 36.8482, 354, 150, '["Maternity", "Neonatal ICU", "Obstetrics"]'::jsonb,
    ST_SetSRID(ST_MakePoint(36.8482, -1.2825), 4326)
),
(
    '13065', 'Mama Lucy Kibaki Hospital', 'County Referral Hospital', 'Level 5',
    'County Government of Nairobi', 'Public', 'Operational', 'Nairobi', 'Embakasi Central', 'Komarock',
    -1.2780, 36.8920, 200, 25, '["Emergency", "Maternity", "General Surgery"]'::jsonb,
    ST_SetSRID(ST_MakePoint(36.8920, -1.2780), 4326)
),
(
    '13201', 'Kibera South Health Centre', 'Health Centre', 'Level 3',
    'Faith Based / NGO', 'Faith Based', 'Operational', 'Nairobi', 'Kibra', 'Makina',
    -1.3142, 36.7865, 15, 2, '["Emergency Stabilization", "Maternal Care"]'::jsonb,
    ST_SetSRID(ST_MakePoint(36.7865, -1.3142), 4326)
),
(
    '13144', 'Mukuru Health Centre', 'Health Centre', 'Level 3',
    'County Government of Nairobi', 'Public', 'Operational', 'Nairobi', 'Embakasi South', 'Kwa Njenga',
    -1.3320, 36.8780, 25, 4, '["Outpatient", "Immunization", "Antenatal"]'::jsonb,
    ST_SetSRID(ST_MakePoint(36.8780, -1.3320), 4326)
),
(
    '13250', 'Ruai Dispensary', 'Dispensary', 'Level 2',
    'County Government of Nairobi', 'Public', 'Operational', 'Nairobi', 'Kasarani', 'Ruai',
    -1.2650, 36.9850, 4, 1, '["Basic Outpatient", "Immunization"]'::jsonb,
    ST_SetSRID(ST_MakePoint(36.9850, -1.2650), 4326)
)
ON CONFLICT (facility_code) DO NOTHING;


-- 3. Analysis Regions (matching wards)
INSERT INTO analysis_regions (name, region_type, admin_id, area_sq_km, centroid, geom)
SELECT 
    name, 'ward', id, area_sq_km, ST_Centroid(geom), geom
FROM administrative_boundaries
WHERE level = 'ward';


-- 4. Initial Demo Analysis Run
INSERT INTO analysis_runs (id, query, run_type, demo_area, status, parameters, result_summary)
VALUES (
    1, 
    'Which populated areas have poor geographic access to healthcare in Nairobi?',
    'accessibility',
    'Nairobi County',
    'completed',
    '{"threshold_km": 5, "decay_function": "linear", "weights": {"distance": 0.6, "capacity": 0.4}}'::jsonb,
    '{"total_regions": 4, "critical": 1, "limited": 1, "moderate": 1, "excellent": 1}'::jsonb
)
ON CONFLICT (id) DO NOTHING;


-- 5. Accessibility Results
INSERT INTO accessibility_results (
    run_id, region_id, nearest_facility_id, nearest_facility_name, distance_meters, 
    travel_time_minutes, facility_count_5km, facility_count_10km, population_covered, 
    accessibility_score, accessibility_category, factors
) VALUES
(
    1,
    (SELECT id FROM analysis_regions WHERE name = 'Kenyatta Golf Course'),
    (SELECT id FROM health_facilities WHERE facility_code = '13023'),
    'Kenyatta National Hospital',
    450.0, 5.2, 8, 24, 38400, 92.5, 'excellent',
    '{"proximity_factor": "optimal", "nearest_keph": "Level 6"}'::jsonb
),
(
    1,
    (SELECT id FROM analysis_regions WHERE name = 'Makina'),
    (SELECT id FROM health_facilities WHERE facility_code = '13201'),
    'Kibera South Health Centre',
    1200.0, 18.5, 5, 19, 72500, 52.0, 'moderate',
    '{"proximity_factor": "moderate", "congestion_factor": "high"}'::jsonb
),
(
    1,
    (SELECT id FROM analysis_regions WHERE name = 'Kwa Njenga'),
    (SELECT id FROM health_facilities WHERE facility_code = '13144'),
    'Mukuru Health Centre',
    2400.0, 24.0, 3, 11, 84100, 34.0, 'limited',
    '{"proximity_factor": "limited", "inpatient_shortage": "severe"}'::jsonb
),
(
    1,
    (SELECT id FROM analysis_regions WHERE name = 'Ruai'),
    (SELECT id FROM health_facilities WHERE facility_code = '13250'),
    'Ruai Dispensary',
    7800.0, 48.0, 1, 2, 46200, 14.5, 'critical',
    '{"proximity_factor": "critical_distance", "nearest_hospital_km": 18.2}'::jsonb
)
ON CONFLICT (run_id, region_id) DO NOTHING;


-- 6. Spatial Findings (AI Evidence)
INSERT INTO spatial_findings (run_id, region_id, finding_type, severity, title, description, evidence, recommendations, geom)
VALUES
(
    1,
    (SELECT id FROM analysis_regions WHERE name = 'Ruai'),
    'desert',
    'critical',
    'Critical Hospital Desert in Ruai Zone',
    'Ruai ward has over 46,000 residents whose nearest referral hospital is over 18 km away, far exceeding the WHO standard 5 km radius.',
    '{"distance_to_level_4": 18200, "estimated_ambulance_delay_min": 55, "facilities_ratio": "0.02 per 1000"}'::jsonb,
    '["Upgrade Ruai Dispensary to a Level 4 Sub-County Hospital", "Deploy mobile emergency clinic along Kangundo corridor"]'::jsonb,
    (SELECT geom FROM analysis_regions WHERE name = 'Ruai')
),
(
    1,
    (SELECT id FROM analysis_regions WHERE name = 'Kwa Njenga'),
    'underserved_density',
    'high',
    'Severe High-Density Bottleneck in Mukuru',
    'Kwa Njenga has 84,100 residents served predominantly by a single Level 3 facility with only 25 beds.',
    '{"bed_to_pop_ratio": "0.3 per 1000", "recommended_ratio": "2.0 per 1000"}'::jsonb,
    '["Construct satellite maternity wing at Mukuru", "Improve emergency access transit lanes"]'::jsonb,
    (SELECT geom FROM analysis_regions WHERE name = 'Kwa Njenga')
);
