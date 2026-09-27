# GeoMind AI — Database Layer

> **AI-powered geospatial intelligence platform** for healthcare accessibility analysis in Kenya.

## Quick Start

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- Python 3.10+ (for data pipeline scripts)
- Git

### 1. Clone & Configure
```bash
git clone <repo-url>
cd GeoMind-database
cp .env.example .env
# Edit .env if you need to change default credentials
```

### 2. Start PostGIS
```bash
docker compose up -d
```
This starts PostgreSQL 16 + PostGIS 3.4 and automatically:
- Creates the `geomind` database
- Enables the PostGIS extension
- Creates all schema tables with spatial indexes
- Seeds lookup/reference data

### 3. Verify
```bash
docker exec -it geomind-db psql -U geomind -d geomind -c "SELECT PostGIS_Full_Version();"
docker exec -it geomind-db psql -U geomind -d geomind -c "\dt"
```

### 4. Load Data
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the data pipeline
python scripts/import_health_facilities.py
python scripts/import_admin_boundaries.py
python scripts/import_roads.py
```

### 5. Test Spatial Queries
```bash
docker exec -it geomind-db psql -U geomind -d geomind -f /docker-entrypoint-initdb.d/03_sample_queries.sql
```

---

## Project Structure

```
GeoMind-database/
├── docker-compose.yml          # PostGIS container definition
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
├── database/
│   ├── init/                   # Auto-run on first container start
│   │   ├── 01_extensions.sql   # PostGIS extension setup
│   │   ├── 02_schema.sql       # Full schema DDL
│   │   └── 03_sample_queries.sql # Validated spatial queries
│   ├── migrations/             # Schema change scripts
│   └── seeds/                  # Reference/seed data
├── scripts/                    # Data pipeline scripts
│   ├── import_health_facilities.py
│   ├── import_admin_boundaries.py
│   ├── import_roads.py
│   └── export_geojson.py
├── data/
│   ├── raw/                    # Original downloaded files (git-ignored)
│   ├── processed/              # Cleaned files (git-ignored)
│   ├── sample/                 # Small sample GeoJSON for frontend dev
│   └── README.md               # Dataset register & documentation
├── docs/
│   ├── schema.md               # Schema documentation
│   ├── api_contract.md         # GeoJSON/API response contracts
│   └── spatial_queries.md      # Query documentation
└── README.md                   # This file
```

## Demo Area
**Nairobi County, Kenya** — urban setting with dense health facility coverage, multiple administrative levels (sub-counties, wards), and good data availability.

## Team
| Member | Role |
|---|---|
| Technical Lead | Backend, FastAPI, Spatial Analysis, Architecture |
| **Eric** | **Database Engineer & Repo Master** |
| Stacy | Research & UI/UX Lead |
| Alberto | Frontend Engineer (Angular) |

## Technology Stack
- **Database:** PostgreSQL 16 + PostGIS 3.4
- **Container:** Docker / Docker Compose
- **Pipeline:** Python (psycopg2, geopandas, requests)
- **Frontend:** Angular (Alberto)
- **Backend:** FastAPI (Technical Lead)
- **Geospatial:** PostGIS, GeoJSON, SRID 4326

## License
Hackathon project — GOMYCODE Come. Build. With AI.
