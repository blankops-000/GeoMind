# GeoMind AI — Dataset Register

> All datasets used in the GeoMind healthcare accessibility MVP.  
> Demo area: **Nairobi County, Kenya**

---

## 1. 🏥 Health Facilities

| Field | Value |
|---|---|
| **Dataset** | Kenya Master Health Facility Registry (KMHFR) |
| **Provider** | Ministry of Health, Kenya |
| **Source URL** | http://kmhfr.health.go.ke / ArcGIS FeatureServer |
| **API Endpoint** | `https://services5.arcgis.com/XGXQEX3dSjCZQoLu/arcgis/rest/services/KMHFR_Health_Facilities/FeatureServer/0/query` |
| **Format** | GeoJSON (via ArcGIS REST API) / CSV download |
| **CRS/SRID** | EPSG:4326 (WGS 84) |
| **Geographic Coverage** | All Kenya; filtered to Nairobi County |
| **Key Fields** | `facility_code`, `name`, `facility_type`, `keph_level`, `owner`, `owner_type`, `county`, `subcounty`, `ward`, `latitude`, `longitude`, `operational_status` |
| **Approx Records** | ~1,000–1,500 facilities in Nairobi County |
| **License** | Government open data (Kenya Open Data Initiative) |
| **Date Accessed** | TBD |
| **Cleaning Performed** | Remove duplicates by facility_code; drop records missing lat/lon; validate coordinates are within Nairobi bounding box; standardize facility_type and owner_type values |
| **Known Limitations** | Some facilities may be closed but listed as operational; coordinates may be approximate; services list may be incomplete |

---

## 2. 🗺️ Administrative Boundaries

| Field | Value |
|---|---|
| **Dataset** | Kenya Administrative Boundaries (County, Sub-County, Ward) |
| **Provider** | Kenya Open Data / Humanitarian Data Exchange (HDX) |
| **Source URL** | https://data.humdata.org/dataset/cod-ab-ken |
| **Format** | GeoJSON / Shapefile |
| **CRS/SRID** | EPSG:4326 (WGS 84) |
| **Geographic Coverage** | All Kenya; filtered to Nairobi County hierarchy |
| **Key Fields** | `adm1_name` (county), `adm2_name` (sub-county), `adm3_name` (ward), `adm_code`, geometry |
| **Approx Records** | 1 county + 17 sub-counties + 85 wards for Nairobi |
| **License** | CC BY / Government open data |
| **Date Accessed** | TBD |
| **Cleaning Performed** | Validate geometries (ST_IsValid); fix topology errors; standardize name casing; build parent-child hierarchy |
| **Known Limitations** | Boundary updates may not reflect latest gazette changes |

---

## 3. 👥 Population Estimates

| Field | Value |
|---|---|
| **Dataset** | WorldPop Kenya Population (constrained, UN-adjusted) |
| **Provider** | WorldPop / University of Southampton |
| **Source URL** | https://hub.worldpop.org/geodata/listing?id=69 |
| **Format** | GeoTIFF (raster) |
| **CRS/SRID** | EPSG:4326 (WGS 84) |
| **Resolution** | 100m or 1km grid |
| **Geographic Coverage** | All Kenya; clipped to Nairobi County |
| **Key Fields** | Pixel value = estimated population count |
| **License** | CC BY 4.0 |
| **Date Accessed** | TBD |
| **Cleaning Performed** | Clip to Nairobi extent; convert raster to point grid (cell centroids); aggregate to analysis regions; remove NoData cells |
| **Known Limitations** | Modeled estimates, not census counts; may undercount informal settlements; temporal mismatch with facility data |

---

## 4. 🛣️ Road Network

| Field | Value |
|---|---|
| **Dataset** | OpenStreetMap Road Network |
| **Provider** | OpenStreetMap Contributors |
| **Source URL** | https://overpass-turbo.eu / Overpass API |
| **Overpass Query** | `[out:json][timeout:120]; area["name"="Nairobi"]["admin_level"="4"]->.searchArea; way["highway"](area.searchArea); out body; >; out skel qt;` |
| **Format** | GeoJSON (converted from OSM) |
| **CRS/SRID** | EPSG:4326 (WGS 84) |
| **Geographic Coverage** | Nairobi County |
| **Key Fields** | `osm_id`, `name`, `highway` (road class), `surface`, `lanes`, `oneway` |
| **Approx Records** | ~50,000–100,000 road segments |
| **License** | ODbL (Open Data Commons Open Database License) |
| **Date Accessed** | TBD |
| **Cleaning Performed** | Filter to major road classes (motorway through residential); remove footpaths/tracks unless needed; compute segment lengths |
| **Known Limitations** | Volunteer-contributed; coverage varies; some roads may be missing or misclassified |

---

## 5. 🛰️ Satellite Imagery

| Field | Value |
|---|---|
| **Dataset** | Sentinel-2 Level-2A (Surface Reflectance) |
| **Provider** | European Space Agency (ESA) / Copernicus |
| **Source URL** | https://dataspace.copernicus.eu |
| **Format** | GeoTIFF (raster, multi-band) |
| **CRS/SRID** | UTM zone (reprojected to EPSG:4326 for analysis) |
| **Resolution** | 10m (visible bands), 20m (vegetation/SWIR) |
| **Geographic Coverage** | Nairobi County tiles |
| **Key Bands** | B02 (Blue), B03 (Green), B04 (Red), B08 (NIR) |
| **License** | Copernicus Open Access (free for any use) |
| **Date Accessed** | TBD |
| **Processing** | Cloud masking, true-color composite, NDVI computation, building detection (CV model) |
| **Known Limitations** | Cloud cover in tropical areas; revisit time ~5 days; requires Copernicus account |
| **Storage** | Filesystem only — metadata in PostGIS `satellite_imagery` table |

---

## 6. 🏘️ Settlements / Buildings (Optional)

| Field | Value |
|---|---|
| **Dataset** | OpenStreetMap Buildings & Places |
| **Provider** | OpenStreetMap Contributors |
| **Source URL** | Overpass API |
| **Format** | GeoJSON |
| **License** | ODbL |
| **Usage** | Contextual layer for settlement identification |

---

## Bounding Box — Nairobi County

```
West:  36.65°E
East:  37.10°E
South: -1.45°S
North: -1.15°S
```

EPSG: 4326 (WGS 84)

---

## Reproduction Steps

1. Run `scripts/import_health_facilities.py` — downloads from KMHFR ArcGIS endpoint
2. Run `scripts/import_admin_boundaries.py` — downloads from HDX
3. Run `scripts/import_roads.py` — queries Overpass API
4. Population raster: manually download from WorldPop, then run processing script
5. Sentinel-2: manually download from Copernicus Data Space, store in `data/raw/satellite/`

All import scripts are idempotent (safe to re-run).
