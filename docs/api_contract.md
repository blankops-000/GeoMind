# GeoMind AI — API & GeoJSON Contract Specification

> **Target Audience:** Alberto (Frontend Engineer - Angular), Technical Lead (Backend Engineer - FastAPI), and Eric (Database Engineer)  
> **Protocol:** REST JSON / GeoJSON (RFC 7946)  
> **CRS / Projection:** EPSG:4326 (WGS 84, Longitude / Latitude order)

---

## 1. Architecture Flow

```
Angular Frontend (Alberto)
       │
       ▼  HTTP / REST (JSON & GeoJSON)
FastAPI Backend (Technical Lead)
       │
       ▼  SQL & Spatial Procedures (ST_AsGeoJSON)
PostgreSQL / PostGIS (Eric)
       │
       ▼  Aggregated Stats & Geometries
AI / Brev Insight Engine (NVIDIA Brev / LLM)
```

> **Note:** The frontend never connects directly to PostgreSQL. All spatial data flows through FastAPI as standardized GeoJSON FeatureCollections.

---

## 2. API Endpoints

### 2.1 Health Facilities Endpoint

* **Endpoint:** `GET /api/v1/facilities`
* **Query Parameters:**
  * `county` (string, optional, default: `"Nairobi"`)
  * `facility_type` (string, optional, e.g. `"Hospital"`, `"Health Centre"`, `"Dispensary"`)
  * `owner_type` (string, optional, e.g. `"Public"`, `"Private"`, `"Faith Based"`)
  * `operational_status` (string, optional, default: `"Operational"`)
* **Response Type:** `application/geo+json`

#### Response Payload:
```json
{
  "type": "FeatureCollection",
  "metadata": {
    "total_features": 128,
    "county": "Nairobi",
    "crs": "EPSG:4326"
  },
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [36.8078, -1.3015]
      },
      "properties": {
        "id": 101,
        "facility_code": "13023",
        "name": "Kenyatta National Hospital",
        "facility_type": "National Referral Hospital",
        "keph_level": "Level 6",
        "ownership": "Ministry of Health",
        "owner_type": "Public",
        "status": "Operational",
        "subcounty": "Kibra",
        "ward": "Kenyatta Golf Course",
        "beds": 1800,
        "services": ["Emergency", "ICU", "Maternity", "Surgical", "Radiology"]
      }
    }
  ]
}
```

---

### 2.2 Administrative Boundaries Endpoint

* **Endpoint:** `GET /api/v1/boundaries`
* **Query Parameters:**
  * `level` (string, required: `'county'` | `'subcounty'` | `'ward'`)
  * `parent_id` (integer, optional)
* **Response Type:** `application/geo+json`

#### Response Payload:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [
          [
            [
              [36.850, -1.280],
              [36.865, -1.282],
              [36.860, -1.295],
              [36.845, -1.290],
              [36.850, -1.280]
            ]
          ]
        ]
      },
      "properties": {
        "id": 4701,
        "name": "Kibra",
        "level": "subcounty",
        "code": "KE047_KIB",
        "area_sq_km": 12.1,
        "population": 185777
      }
    }
  ]
}
```

---

### 2.3 Accessibility Scoring & Heatmap Endpoint

* **Endpoint:** `GET /api/v1/accessibility`
* **Query Parameters:**
  * `run_id` (integer, optional, defaults to latest run)
  * `category` (string, optional: `'excellent'` | `'good'` | `'moderate'` | `'limited'` | `'critical'`)
* **Response Type:** `application/geo+json`

#### Response Payload:
```json
{
  "type": "FeatureCollection",
  "metadata": {
    "run_id": 14,
    "demo_area": "Nairobi County",
    "generated_at": "2026-09-27T16:00:00Z"
  },
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [[[[36.81, -1.30], [36.83, -1.30], [36.83, -1.32], [36.81, -1.32], [36.81, -1.30]]]]
      },
      "properties": {
        "id": 802,
        "name": "Kibra South",
        "type": "ward",
        "accessibility_score": 38.5,
        "accessibility_category": "limited",
        "nearest_facility": "Mbagathi County Hospital",
        "distance_meters": 2840.0,
        "travel_time_minutes": 22.0,
        "facilities_within_5km": 3,
        "facilities_within_10km": 12,
        "population": 64200,
        "factors": {
          "terrain_impedance": "low",
          "road_density_km_per_sq_km": 1.4,
          "public_transport_access": "moderate"
        }
      }
    }
  ]
}
```

---

### 2.4 Natural Language AI Query Endpoint

* **Endpoint:** `POST /api/v1/query`
* **Request Body:**
```json
{
  "query": "Which wards in Nairobi have the worst access to emergency health facilities?",
  "session_id": "b8f5e6a1-9a72-4d2c-88e2-63b72c91a021"
}
```

#### Response Payload:
```json
{
  "query": "Which wards in Nairobi have the worst access to emergency health facilities?",
  "run_id": 15,
  "summary": {
    "total_wards_analyzed": 85,
    "critical_wards_count": 6,
    "most_underserved_ward": "Ruai",
    "average_distance_km": 4.8
  },
  "ai_insight": {
    "headline": "Severe Emergency Healthcare Deficit in East Nairobi",
    "findings": [
      "Ruai and Njiru wards have average travel distances exceeding 8.5 km to the nearest Level 4+ hospital.",
      "Road density in peripheral eastern zones slows ambulance transit times by an estimated 35% compared to central subcounties."
    ],
    "recommendations": [
      "Prioritize upgrade of existing Ruai Dispensary to a 24-hour urgent care facility.",
      "Station dedicated emergency transit ambulances along Kangundo Road corridor."
    ]
  },
  "map_layers": {
    "highlight_regions": "/api/v1/accessibility?run_id=15&category=critical",
    "facilities": "/api/v1/facilities?facility_type=Hospital"
  }
}
```

---

## 3. MapLibre / Angular Integration Guidelines for Alberto

1. **Map Projection & Center:**
   * Center: `[36.8219, -1.2921]` (Nairobi City Center)
   * Zoom: `11` - `12`
   * Coordinate order in GeoJSON is always `[Longitude, Latitude]`.

2. **Choropleth Color Scale for `accessibility_category`:**
   * `excellent`: `#10B981` (Emerald Green)
   * `good`: `#3B82F6` (Blue)
   * `moderate`: `#F59E0B` (Amber)
   * `limited`: `#F97316` (Orange)
   * `critical`: `#EF4444` (Rose / Red)

3. **Symbology for Health Facilities:**
   * Level 5/6 Hospitals: Circle Radius 8, Border `#1E293B`, Fill `#2563EB`
   * Health Centres / Dispensaries: Circle Radius 5, Fill `#0284C7`
   * Private / Clinic: Circle Radius 4, Fill `#94A3B8`
