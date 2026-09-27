# GeoMind AI

GeoMind AI is an AI-powered geospatial intelligence platform.
Geographic computation produces measurable evidence using PostGIS and Computer Vision, and AI interprets that evidence.

## Backend Architecture Summary

The backend is built as a modular monolith using Python 3.11+, FastAPI, PostgreSQL + PostGIS, GeoPandas/Shapely, and CPU-friendly Computer Vision pipelines.

## Setup Instructions

1. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

2. Start database service:
   ```bash
   docker-compose up -d db
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run unit tests:
   ```bash
   python -m pytest tests/unit
   ```

## Phase Status

Phase 1 complete — foundation and contracts frozen

> [!IMPORTANT]
> **Note for Downstream Agents:**
> Do not modify `app/schemas/*.py`. These are frozen contracts.
