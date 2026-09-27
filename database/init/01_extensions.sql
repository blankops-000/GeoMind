-- ============================================================
-- GeoMind AI — 01_extensions.sql
-- Enable required PostgreSQL extensions
-- Runs automatically on first container start
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS pg_trgm;       -- Fuzzy text search (facility names)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- UUID generation

-- Verify PostGIS is active
SELECT PostGIS_Full_Version();
