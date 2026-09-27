const fs = require('fs');
const path = require('path');
const { Client } = require('pg');

const DB_URL = process.env.DATABASE_URL || "postgresql://geomind_user:Ri3FwuZVLuaY0zvl82eNItvPB88Dxxgw@dpg-dasj3qfpn0mc738kli2g-a.singapore-postgres.render.com/geomind";

const BASE_DIR = path.resolve(__dirname, '..');
const DATASETS_DIR = path.join(BASE_DIR, 'GeoMind_Datasets');
const INIT_DIR = path.join(BASE_DIR, 'database', 'init');

function readJsonFile(filePath) {
    let content = fs.readFileSync(filePath, 'utf-8');
    if (content.charCodeAt(0) === 0xFEFF) {
        content = content.slice(1);
    }
    return JSON.parse(content.trim());
}

async function main() {
    console.log("==================================================================");
    console.log("               GeoMind AI — Database Setup Engine                 ");
    console.log("==================================================================");
    
    console.log("\n[1/6] Connecting to Render PostgreSQL instance...");
    const client = new Client({
        connectionString: DB_URL,
        ssl: { rejectUnauthorized: false }
    });

    try {
        await client.connect();
        const verRes = await client.query("SELECT version();");
        console.log(`  [OK] Connected successfully! (${verRes.rows[0].version.split(',')[0]})`);
    } catch (err) {
        console.error(`  [FATAL] Database connection failed:`, err.message);
        process.exit(1);
    }

    // 2. Extensions & Schema
    console.log("\n[2/6] Initializing Extensions & Schema...");
    const extensions = ['postgis', 'postgis_topology', 'pg_trgm', 'uuid-ossp'];
    for (const ext of extensions) {
        try {
            await client.query(`CREATE EXTENSION IF NOT EXISTS "${ext}";`);
            console.log(`  [x] Extension enabled: ${ext}`);
        } catch (e) {
            console.log(`  [!] Extension note: ${e.message}`);
        }
    }

    let schemaSql = fs.readFileSync(path.join(INIT_DIR, '02_schema.sql'), 'utf-8');
    if (schemaSql.charCodeAt(0) === 0xFEFF) schemaSql = schemaSql.slice(1);
    await client.query(schemaSql);
    console.log("  [x] Complete schema tables, indexes, views, and functions created.");

    // 3. Health Facilities Ingestion
    console.log("\n[3/6] Ingesting Health Facilities...");
    const hfPath = path.join(DATASETS_DIR, '01_health_facilities', 'health_facilities.geojson');
    if (fs.existsSync(hfPath)) {
        const hfData = readJsonFile(hfPath);
        const features = hfData.features || [];
        console.log(`  Read ${features.length} facility records from GeoJSON.`);

        const batchSize = 100;
        for (let i = 0; i < features.length; i += batchSize) {
            const batch = features.slice(i, i + batchSize);
            for (const f of batch) {
                const p = f.properties || {};
                const coords = f.geometry?.coordinates || [0, 0];
                const lon = coords[0];
                const lat = coords[1];
                const fCode = p.facility_code || `OSM_${p.id}`;

                await client.query(`
                    INSERT INTO health_facilities (
                        facility_code, name, facility_type, keph_level, ownership, owner_type,
                        operational_status, county, latitude, longitude, geom
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, ST_SetSRID(ST_MakePoint($11, $12), 4326))
                    ON CONFLICT (facility_code) DO UPDATE SET
                        name = EXCLUDED.name,
                        facility_type = EXCLUDED.facility_type,
                        keph_level = EXCLUDED.keph_level,
                        ownership = EXCLUDED.ownership,
                        owner_type = EXCLUDED.owner_type,
                        operational_status = EXCLUDED.operational_status,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        geom = EXCLUDED.geom;
                `, [
                    fCode, p.name || 'Health Facility', p.facility_type || 'Health Centre',
                    p.keph_level || 'Level 2', p.ownership || 'Public/Private', p.owner_type || 'Private',
                    'Operational', 'Nairobi', lat, lon, lon, lat
                ]);
            }
        }
        const countRes = await client.query("SELECT COUNT(*) FROM health_facilities;");
        console.log(`  [x] ${countRes.rows[0].count} Health facilities stored in PostGIS.`);
    }

    // 4. Boundaries & Roads
    console.log("\n[4/6] Ingesting Boundaries & Road Network...");
    const countiesPath = path.join(DATASETS_DIR, '02_boundaries', 'counties.geojson');
    if (fs.existsSync(countiesPath)) {
        const cData = readJsonFile(countiesPath);
        for (const feat of cData.features || []) {
            const p = feat.properties || {};
            const name = p.shapeName || p.COUNTY || p.name || 'County';
            const code = p.shapeID || p.ADM1_PCODE || `KEN_ADM1_${name}`;
            await client.query(`
                INSERT INTO administrative_boundaries (name, level, code, geom)
                VALUES ($1, 'county', $2, ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON($3), 4326)))
                ON CONFLICT (code) DO NOTHING;
            `, [name, code, JSON.stringify(feat.geometry)]);
        }
        console.log("  [x] Counties loaded.");
    }

    const subPath = path.join(DATASETS_DIR, '02_boundaries', 'subcounties.geojson');
    if (fs.existsSync(subPath)) {
        const sData = readJsonFile(subPath);
        for (const feat of sData.features || []) {
            const p = feat.properties || {};
            const name = p.shapeName || p.SUBCOUNTY || p.name || 'Subcounty';
            const code = p.shapeID || p.ADM2_PCODE || `KEN_ADM2_${name}`;
            await client.query(`
                INSERT INTO administrative_boundaries (name, level, code, geom)
                VALUES ($1, 'subcounty', $2, ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON($3), 4326)))
                ON CONFLICT (code) DO NOTHING;
            `, [name, code, JSON.stringify(feat.geometry)]);
        }
        console.log("  [x] Sub-counties loaded.");
    }

    const wardsPath = path.join(DATASETS_DIR, '02_boundaries', 'wards.geojson');
    if (fs.existsSync(wardsPath)) {
        const wData = readJsonFile(wardsPath);
        for (const feat of wData.features || []) {
            const p = feat.properties || {};
            const name = p.name || 'Ward';
            const code = p.code || `WARD_${name}`;
            await client.query(`
                INSERT INTO administrative_boundaries (name, level, code, population, area_sq_km, geom)
                VALUES ($1, 'ward', $2, $3, $4, ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON($5), 4326)))
                ON CONFLICT (code) DO UPDATE SET
                    population = EXCLUDED.population,
                    area_sq_km = EXCLUDED.area_sq_km,
                    geom = EXCLUDED.geom;
            `, [name, code, p.population, p.area_sq_km, JSON.stringify(feat.geometry)]);
        }
        console.log("  [x] Wards loaded.");
    }

    await client.query(`
        INSERT INTO analysis_regions (name, region_type, admin_id, area_sq_km, centroid, geom)
        SELECT name, 'ward', id, area_sq_km, ST_Centroid(geom), geom
        FROM administrative_boundaries
        WHERE level = 'ward'
        ON CONFLICT DO NOTHING;
    `);
    console.log("  [x] Analysis regions synchronized with wards.");

    const roadsPath = path.join(DATASETS_DIR, '04_roads', 'roads.geojson');
    if (fs.existsSync(roadsPath)) {
        const rData = readJsonFile(roadsPath);
        for (const feat of rData.features || []) {
            const p = feat.properties || {};
            if (p.osm_id) {
                await client.query(`
                    INSERT INTO roads (osm_id, name, road_class, surface, geom)
                    VALUES ($1, $2, $3, $4, ST_SetSRID(ST_GeomFromGeoJSON($5), 4326))
                    ON CONFLICT (osm_id) DO NOTHING;
                `, [p.osm_id, p.name || 'Unnamed Road', p.road_class || 'primary', p.surface || 'paved', JSON.stringify(feat.geometry)]);
            }
        }
        await client.query("UPDATE roads SET length_meters = ST_Length(geom::geography) WHERE length_meters IS NULL;");
        const rRes = await client.query("SELECT COUNT(*) AS cnt, ROUND(SUM(length_meters)/1000, 1) AS km FROM roads;");
        console.log(`  [x] ${rRes.rows[0].cnt} road segments loaded (${rRes.rows[0].km} km total).`);
    }

    await client.query(`
        INSERT INTO population_points (grid_id, population, resolution_m, year, geom) VALUES
        ('NBO_POP_001', 38400, 100, 2025, ST_SetSRID(ST_MakePoint(36.8078, -1.3015), 4326)),
        ('NBO_POP_002', 72500, 100, 2025, ST_SetSRID(ST_MakePoint(36.7865, -1.3142), 4326)),
        ('NBO_POP_003', 84100, 100, 2025, ST_SetSRID(ST_MakePoint(36.8780, -1.3320), 4326)),
        ('NBO_POP_004', 46200, 100, 2025, ST_SetSRID(ST_MakePoint(36.9850, -1.2650), 4326))
        ON CONFLICT (grid_id) DO NOTHING;
    `);

    await client.query(`
        INSERT INTO satellite_imagery (scene_id, satellite, acquisition_date, cloud_cover_pct, resolution_m, bands, bbox) VALUES
        ('S2A_MSIL2A_20260815T073621_R092_T37MBU', 'Sentinel-2A', '2026-08-15', 2.4, 10.0, ARRAY['B02','B03','B04','B08'], ST_SetSRID(ST_MakePolygon(ST_GeomFromText('LINESTRING(36.65 -1.45, 37.10 -1.45, 37.10 -1.15, 36.65 -1.15, 36.65 -1.45)')), 4326)),
        ('S2B_MSIL2A_20260920T073619_R092_T37MBU', 'Sentinel-2B', '2026-09-20', 1.8, 10.0, ARRAY['B02','B03','B04','B08'], ST_SetSRID(ST_MakePolygon(ST_GeomFromText('LINESTRING(36.65 -1.45, 37.10 -1.45, 37.10 -1.15, 36.65 -1.15, 36.65 -1.45)')), 4326))
        ON CONFLICT (scene_id) DO NOTHING;
    `);
    console.log("  [x] Population grid and Sentinel-2 footprints loaded.");

    // 5. Spatial Scoring Engine
    console.log("\n[5/6] Executing Spatial Accessibility Scoring Engine...");
    const runRes = await client.query(`
        INSERT INTO analysis_runs (query, run_type, demo_area, status, parameters, started_at)
        VALUES (
            'Which populated areas have poor geographic access to healthcare in Nairobi?',
            'accessibility',
            'Nairobi County',
            'running',
            '{"threshold_km": 5, "distance_decay": "exponential", "hospital_weight": 0.6}'::jsonb,
            NOW()
        ) RETURNING id;
    `);
    const runId = runRes.rows[0].id;
    console.log(`  Analysis Run ID: #${runId}`);

    await client.query(`
        INSERT INTO accessibility_results (
            run_id, region_id, nearest_facility_id, nearest_facility_name, distance_meters,
            travel_time_minutes, facility_count_5km, facility_count_10km, population_covered,
            accessibility_score, accessibility_category, factors
        )
        SELECT 
            $1 AS run_id,
            r.id AS region_id,
            h.id AS nearest_facility_id,
            h.name AS nearest_facility_name,
            ROUND(ST_Distance(ST_Centroid(r.geom)::geography, h.geom::geography)::numeric, 1) AS distance_meters,
            ROUND((ST_Distance(ST_Centroid(r.geom)::geography, h.geom::geography) / 1000.0 * 6.0)::numeric, 1) AS travel_time_minutes,
            (SELECT COUNT(*) FROM health_facilities hf2 WHERE hf2.operational_status = 'Operational' AND ST_DWithin(ST_Centroid(r.geom)::geography, hf2.geom::geography, 5000)) AS facility_count_5km,
            (SELECT COUNT(*) FROM health_facilities hf3 WHERE hf3.operational_status = 'Operational' AND ST_DWithin(ST_Centroid(r.geom)::geography, hf3.geom::geography, 10000)) AS facility_count_10km,
            COALESCE(ab.population, 50000) AS population_covered,
            CASE 
                WHEN ST_Distance(ST_Centroid(r.geom)::geography, h.geom::geography) < 1000 THEN 92.0
                WHEN ST_Distance(ST_Centroid(r.geom)::geography, h.geom::geography) < 3000 THEN 68.0
                WHEN ST_Distance(ST_Centroid(r.geom)::geography, h.geom::geography) < 5000 THEN 45.0
                WHEN ST_Distance(ST_Centroid(r.geom)::geography, h.geom::geography) < 8000 THEN 25.0
                ELSE 12.0
            END AS accessibility_score,
            CASE 
                WHEN ST_Distance(ST_Centroid(r.geom)::geography, h.geom::geography) < 1000 THEN 'excellent'
                WHEN ST_Distance(ST_Centroid(r.geom)::geography, h.geom::geography) < 3000 THEN 'good'
                WHEN ST_Distance(ST_Centroid(r.geom)::geography, h.geom::geography) < 5000 THEN 'moderate'
                WHEN ST_Distance(ST_Centroid(r.geom)::geography, h.geom::geography) < 8000 THEN 'limited'
                ELSE 'critical'
            END AS accessibility_category,
            jsonb_build_object(
                'nearest_type', h.facility_type,
                'nearest_keph', h.keph_level,
                'road_access', 'paved_network'
            ) AS factors
        FROM analysis_regions r
        JOIN administrative_boundaries ab ON r.admin_id = ab.id
        CROSS JOIN LATERAL (
            SELECT id, name, facility_type, keph_level, geom
            FROM health_facilities
            WHERE operational_status = 'Operational' AND geom IS NOT NULL
            ORDER BY ST_Centroid(r.geom) <-> geom
            LIMIT 1
        ) h
        ON CONFLICT (run_id, region_id) DO NOTHING;
    `, [runId]);

    await client.query(`
        INSERT INTO spatial_findings (run_id, region_id, finding_type, severity, title, description, evidence, recommendations, geom)
        SELECT 
            $1,
            ar.region_id,
            CASE WHEN ar.accessibility_category = 'critical' THEN 'desert' ELSE 'underserved_density' END,
            ar.accessibility_category,
            'Identified Healthcare Access Disparity in ' || reg.name,
            'Region ' || reg.name || ' has an average travel distance of ' || ROUND((ar.distance_meters/1000)::numeric, 1) || ' km to the nearest facility (' || ar.nearest_facility_name || ').',
            jsonb_build_object(
                'distance_meters', ar.distance_meters,
                'facilities_within_5km', ar.facility_count_5km,
                'population_at_risk', ar.population_covered
            ),
            jsonb_build_array(
                'Deploy mobile emergency triage unit',
                'Upgrade local dispensary to Level 4 urgent care'
            ),
            reg.geom
        FROM accessibility_results ar
        JOIN analysis_regions reg ON ar.region_id = reg.id
        WHERE ar.run_id = $2 AND ar.accessibility_category IN ('critical', 'limited');
    `, [runId, runId]);

    await client.query(`
        UPDATE analysis_runs SET
            status = 'completed',
            completed_at = NOW(),
            result_summary = (
                SELECT jsonb_build_object(
                    'total_regions_scored', COUNT(*),
                    'critical_count', COUNT(*) FILTER (WHERE accessibility_category = 'critical'),
                    'limited_count', COUNT(*) FILTER (WHERE accessibility_category = 'limited'),
                    'good_count', COUNT(*) FILTER (WHERE accessibility_category IN ('good', 'excellent'))
                ) FROM accessibility_results WHERE run_id = $1
            )
        WHERE id = $2;
    `, [runId, runId]);
    console.log("  [x] Spatial analysis completed successfully.");

    // 6. Verification
    console.log("\n[6/6] Verifying Database & Testing GeoJSON API Output...");
    const tables = [
        'administrative_boundaries',
        'health_facilities',
        'roads',
        'population_points',
        'analysis_regions',
        'analysis_runs',
        'accessibility_results',
        'spatial_findings',
        'satellite_imagery'
    ];

    console.log("\n  " + "=".repeat(50));
    console.log(`  ${'Table Name'.padEnd(30)} | ${'Record Count'.padStart(15)}`);
    console.log("  " + "-".repeat(50));
    for (const tbl of tables) {
        const res = await client.query(`SELECT COUNT(*) AS cnt FROM ${tbl};`);
        console.log(`  ${tbl.padEnd(30)} | ${String(res.rows[0].cnt).padStart(15)}`);
    }
    console.log("  " + "=".repeat(50));

    const geoRes = await client.query("SELECT fn_accessibility_geojson() AS geojson;");
    const feats = geoRes.rows[0]?.geojson?.features?.length || 0;
    console.log(`\n  [x] Tested fn_accessibility_geojson(): generated ${feats} GeoJSON features.`);

    const facRes = await client.query("SELECT fn_facilities_geojson('Nairobi') AS geojson;");
    const facCount = facRes.rows[0]?.geojson?.features?.length || 0;
    console.log(`  [x] Tested fn_facilities_geojson('Nairobi'): generated ${facCount} facility points.`);

    await client.end();
    console.log("\n==================================================================");
    console.log("  RENDER POSTGRESQL DATABASE SETUP COMPLETED SUCCESSFULLY!");
    console.log("==================================================================\n");
}

main().catch(err => {
    console.error("Setup failed:", err);
    process.exit(1);
});
