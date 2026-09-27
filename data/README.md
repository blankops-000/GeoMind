# GeoMind AI — Dataset Register

> All datasets utilized in the GeoMind healthcare accessibility MVP.  
> Demo Area: **Nairobi County, Kenya (EPSG:4326)**  
> Last Verified & Ingested: **September 2026**

---

## 1. 🏥 Health Facilities (KMHFR & OpenStreetMap)

| Field | Value |
|---|---|
| **Dataset** | Kenya Master Health Facility Registry (KMHFR) & OSM Health Layer |
| **Provider** | Ministry of Health, Kenya / OpenStreetMap Contributors / HOTOSM |
| **Raw File** | `data/raw/osm_nairobi_health.json` (519 KB) |
| **Processed File** | `data/processed/nairobi_health_facilities.geojson` (1.42 MB) |
| **Database Seed** | `database/seeds/02_real_datasets_seed.sql` & `database/init/05_real_seed.sql` |
| **CRS / SRID** | EPSG:4326 (WGS 84, Lat/Lon) |
| **Records Ingested** | **1,139 real health facilities** in Nairobi County |
| **Key Attributes** | `facility_code`, `name`, `facility_type` (Hospital, Clinic, Health Centre, Pharmacy), `keph_level` (Level 2 to Level 6), `ownership`, `owner_type` (Public/Private), `operational_status`, `geometry` (Point) |
| **License** | Open Database License (ODbL) / Kenya Open Data |
| **Cleaning Performed** | Deduplication, coordinate verification within Nairobi bounding box, standardization of facility levels and ownership classifications. |

---

## 2. 🗺️ Administrative Boundaries (Counties & Sub-Counties)

| Field | Value |
|---|---|
| **Dataset** | Kenya Administrative Boundaries (ADM1 & ADM2) |
| **Provider** | geoBoundaries / Humanitarian Data Exchange (HDX) / Kenya Open Data |
| **Raw Files** | `data/raw/kenya_adm1_counties.geojson` (861 KB), `data/raw/kenya_adm2_subcounties.geojson` (2.03 MB) |
| **Processed File** | `data/processed/nairobi_subcounties.geojson` (179 KB) |
| **CRS / SRID** | EPSG:4326 (WGS 84) |
| **Records Ingested** | **15 Nairobi Sub-counties** (Westlands, Dagoretti, Langata, Kibra, Roysambu, Kasarani, Ruaraka, Embakasi East/West/North/Central/South, Makadara, Kamukunji, Starehe, Mathare) + Nairobi County Boundary |
| **Key Attributes** | `name`, `level` (`subcounty`, `county`), `code`, `geom` (MultiPolygon) |
| **License** | CC BY 4.0 / Open Data Commons |

---

## 3. 🛣️ Road & Transportation Network

| Field | Value |
|---|---|
| **Dataset** | OpenStreetMap Nairobi Major Road Corridors |
| **Provider** | OpenStreetMap Contributors via Overpass API |
| **Raw File** | `data/raw/osm_nairobi_roads.json` (2.99 MB, 2,920 segments) |
| **Processed File** | `data/processed/nairobi_roads_network.geojson` (1.61 MB) |
| **CRS / SRID** | EPSG:4326 (WGS 84) |
| **Key Attributes** | `osm_id`, `name`, `road_class` (`motorway`, `trunk`, `primary`, `secondary`, `tertiary`), `surface`, `geom` (LineString) |
| **Usage** | Distance impedance, network travel accessibility, emergency response transit corridors. |
| **License** | ODbL |

---

## 4. 👥 Population Grid & Distribution

| Field | Value |
|---|---|
| **Dataset** | WorldPop Kenya Modelled Population Grid (100m / 1km resolution) |
| **Provider** | WorldPop Project / University of Southampton |
| **Storage in DB** | `population_points` table in PostGIS (`geom` Point centroids) |
| **CRS / SRID** | EPSG:4326 (WGS 84) |
| **Usage** | Population-weighted catchment analysis, underserved density estimation (`ST_DWithin` aggregations). |
| **License** | Creative Commons Attribution 4.0 International |

---

## 5. 🛰️ Sentinel-2 Satellite Imagery (Evidence & CV Layer)

| Field | Value |
|---|---|
| **Dataset** | Sentinel-2 Level-2A (Surface Reflectance, MSI) |
| **Provider** | European Space Agency (ESA) / Copernicus Data Space Ecosystem |
| **Tile Reference** | Tile `T37MBU` / `T37MBT` (Nairobi Metropolitan Footprint) |
| **Bands** | B02 (Blue), B03 (Green), B04 (Red), B08 (NIR) |
| **Resolution** | 10 meters (Visible / NIR) |
| **Storage Architecture** | File-system raster storage; PostGIS tracks bounding polygons and metadata in `satellite_imagery` table; derived vector features stored in `spatial_findings`. |
| **Computer Vision Use Cases** | Settlement expansion detection, built-up density analysis, environmental accessibility barriers. |
| **License** | Copernicus Open Access |

---

## Summary of Stored Files

```
data/
├── raw/
│   ├── kenya_adm1_counties.geojson       (861 KB)
│   ├── kenya_adm2_subcounties.geojson    (2.03 MB)
│   ├── osm_nairobi_health.json           (519 KB - 1,139 facilities)
│   └── osm_nairobi_roads.json            (2.99 MB - 2,920 road ways)
├── processed/
│   ├── nairobi_subcounties.geojson       (179 KB)
│   ├── nairobi_health_facilities.geojson (1.42 MB)
│   └── nairobi_roads_network.geojson     (1.61 MB)
└── sample/
    ├── sample_nairobi_facilities.geojson (KNH, Nairobi Hosp, Mbagathi, Pumwani, Mama Lucy)
    └── sample_accessibility_results.geojson (Choropleth wards with scoring & factors)
```
