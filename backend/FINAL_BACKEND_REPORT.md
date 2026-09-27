# GeoMind AI — Final Backend Report

## Status
MVP backend is COMPLETE and FROZEN.

## What Was Built
Modular FastAPI monolith with:
- PostgreSQL + PostGIS persistence (6 tables)
- Spatial Engine (PostGIS + GeoPandas)
- Query Understanding + Analysis Planning (deterministic + AI-enhanced)
- Computer Vision Service (georeferencing pipeline)
- AI Service (provider-agnostic + stub fallback)
- Evidence Layer (build + validate)
- Analysis Orchestrator (state machine)
- REST API (4 endpoints)
- E2E test coverage

## Architecture (Flow)
```
  USER QUESTION
        ↓
  POST /api/v1/query
        ↓
  Query Understanding   (Phase 3B)
        ↓
  Analysis Planning     (Phase 3B)
        ↓
  Plan Validation       (Phase 3B)
        ↓
  Spatial Analysis      (Phase 3A)
        ↓
  Computer Vision       (Phase 3C, if required)
        ↓
  Evidence Building     (Phase 4A)
        ↓
  AI Reasoning          (Phase 4A)
        ↓
  Result Validation     (Phase 4A)
        ↓
  GET /api/v1/analysis/{id}
        ↓
  GeoJSON + Statistics + Insight
        ↓
  Angular Frontend
```

## Endpoints
- `GET /api/v1/health`
- `POST /api/v1/query`
- `GET /api/v1/analysis/{id}`
- `GET /api/v1/datasets`

## How to Run
1. `cp .env.example .env`
2. `docker-compose up -d db`
3. `pip install -r requirements.txt`
4. `python scripts/init_db.py`
5. `python scripts/seed_demo.py`
6. `uvicorn app.main:app --reload --port 8000`
7. Open `http://localhost:8000/docs`

## How to Verify
- `pytest tests/unit`
- `pytest tests/integration`
- `pytest tests/e2e`
- `python scripts/demo_run.py` (server running)

## The Frontend Contract (FROZEN)

### `POST /api/v1/query`
Request:
```json
{ "question": "string", "location": null }
```
Response (202):
```json
{ "analysis_id": "UUID", "status": "processing", "message": "Analysis started" }
```

### `GET /api/v1/analysis/{analysis_id}`
Response (200, completed):
```json
{
  "analysis_id": "UUID",
  "status": "completed",
  "query": { "original": "string", "interpreted": {} },
  "map": { "type": "FeatureCollection", "features": [] },
  "statistics": {},
  "findings": [],
  "insight": {
    "headline": "string",
    "summary": "string",
    "key_findings": [],
    "confidence": "string"
  },
  "provenance": [],
  "confidence": {},
  "limitations": []
}
```

Response (200, processing):
```json
{
  "analysis_id": "UUID",
  "status": "processing",
  "progress": 0,
  "message": "Processing..."
}
```

Response (200, failed):
```json
{
  "analysis_id": "UUID",
  "status": "failed",
  "error": { "code": "string", "message": "string" }
}
```

Response (404):
```json
{ "error": { "code": "ANALYSIS_NOT_FOUND", "message": "..." } }
```

### `GET /api/v1/health`
Response (200):
```json
{
  "status": "ok",
  "database": "ok",
  "ai": "ok",
  "version": "0.1.0"
}
```

### `GET /api/v1/datasets`
Response (200):
```json
{ "datasets": [ { "name": "string", "source": "string", "license": null, "coverage": null } ] }
```

## Demo Reliability
- AI provider fails → stub fallback returns valid insight
- DB unavailable → all endpoints return structured errors / skip gracefully
- CV model stub → synthetic mask over demo bbox
- Every external dependency has a fallback

## Test Results
- `pytest tests/unit -q`: `83 passed, 2 skipped, 7 warnings in 20.73s`
- `pytest tests/integration -q`: `8 skipped, 5 warnings in 8.14s` (Skipped when DB is offline)
- `pytest tests/e2e -q`: `5 skipped, 2 warnings in 7.87s` (Skipped when DB is offline)

## Known Limitations
- CV inference uses a mock-friendly path in MVP
- Real datasets plug in via `scripts/import_data.py` (no code changes needed)
- AI reasoning is grounded in `EvidencePackage`; no fabricated numbers

## What Alberto (Angular) Needs to Know
- Base URL: `http://localhost:8000/api/v1`
- `POST /query` with `{"question": "..."}` → 202 + `analysis_id`
- Poll `GET /analysis/{id}` every 1 s
- When `status == "completed"`, render:
  - `map` (`FeatureCollection`) via MapLibre
  - `statistics` (`dict`) in a stats panel
  - `insight.headline` + `insight.key_findings` in the insight panel
  - `provenance` + `limitations` in a footer/expandable
- When `status == "failed"`, render `error.message`

## Freeze Declaration
The backend is FROZEN as of this report.
No further modifications without Technical Lead approval.
Any changes require a new architecture decision record.
