# GeoMind AI — Dataset Sources & Provenance

> **Data Catalog & Provenance Register**  
> Demo Area: **Nairobi County, Kenya**  
> Coordinate Reference System: **EPSG:4326 (WGS 84)**

---

## 1. 01_health_facilities

* **Primary Source:** Kenya Master Health Facility Registry (KMHFR) & OpenStreetMap
* **Provider:** Ministry of Health Kenya / HOTOSM / OSM Contributors
* **URL:** [http://kmhfr.health.go.ke](http://kmhfr.health.go.ke) / [https://data.humdata.org/dataset/hotosm_ken_health_facilities](https://data.humdata.org/dataset/hotosm_ken_health_facilities)
* **License:** Open Database License (ODbL) / Government Open Data
* **Files:**
  * `health_facilities.geojson` (1,139 points)
  * `health_facilities.csv` (Tabular export with capacity & service attributes)

---

## 2. 02_boundaries

* **Primary Source:** geoBoundaries Global Administrative Database & Humanitarian Data Exchange (HDX)
* **Provider:** William & Mary GeoLab / UN OCHA / Kenya Open Data Initiative
* **URL:** [https://www.geoboundaries.org](https://www.geoboundaries.org) / [https://data.humdata.org/dataset/cod-ab-ken](https://data.humdata.org/dataset/cod-ab-ken)
* **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
* **Files:**
  * `counties.geojson` (National 47 counties)
  * `subcounties.geojson` (15 Nairobi Sub-counties)
  * `wards.geojson` (Ward polygons for granular scoring)

---

## 3. 03_population

* **Primary Source:** WorldPop Kenya Modelled Population Grid
* **Provider:** WorldPop Project, University of Southampton
* **URL:** [https://hub.worldpop.org/geodata/listing?id=69](https://hub.worldpop.org/geodata/listing?id=69)
* **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
* **Resolution:** 100m grid resolution
* **Files:**
  * `population.tif` (GeoTIFF raster)

---

## 4. 04_roads

* **Primary Source:** OpenStreetMap Transport Network
* **Provider:** OpenStreetMap Contributors via Overpass API
* **URL:** [https://overpass-turbo.eu](https://overpass-turbo.eu)
* **License:** Open Database License (ODbL)
* **Road Classes:** Motorway, Trunk, Primary, Secondary, Tertiary
* **Files:**
  * `roads.geojson` (300 major arterial corridors)

---

## 5. 05_osm

* **Primary Source:** OpenStreetMap Contextual POIs & Amenities
* **Provider:** OpenStreetMap Contributors
* **License:** ODbL
* **Files:**
  * `osm_data.geojson`

---

## 6. 06_satellite

* **Primary Source:** Sentinel-2 Level-2A (Bottom of Atmosphere Reflectance)
* **Provider:** European Space Agency (ESA) / Copernicus Data Space Ecosystem
* **URL:** [https://dataspace.copernicus.eu](https://dataspace.copernicus.eu)
* **License:** Copernicus Open Access Policy
* **Bands:** B02 (Blue), B03 (Green), B04 (Red), B08 (NIR)
* **Resolution:** 10 meters
* **Tile:** `T37MBU` / `T37MBT`
* **Files:**
  * `imagery_2024.tif` (Baseline satellite scene)
  * `imagery_2026.tif` (Current satellite scene for change detection)

---

## 7. 07_metadata

* `datasets.json` — Machine-readable dataset catalog
* `sources.md` — This provenance documentation
