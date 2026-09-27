"""Spatial Engine Service for PostGIS + GeoPandas spatial processing."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import time
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import text
from sqlalchemy.orm import Session
import shapely.geometry
from shapely.geometry import shape, mapping, Polygon, Point, MultiPolygon

from app.schemas.plan import AnalysisPlan, SpatialOperation
from app.core.config import settings
from app.core.errors import GeoMindError, ErrorCode
from app.utils.crs import bbox_to_polygon, DEFAULT_SRID
from app.utils.geometry import to_geojson_dict, from_geojson_dict, validate_geometry
from app.services.spatial.statistics import (
    region_area_km2,
    facility_count,
    facilities_by_type,
    facilities_in_region_count,
    avg_facility_distance_to_point,
    density_per_km2,
)

SUPPORTED_SPATIAL_OPS = {
    "intersection", "within", "dwithin", "buffer",
    "area", "count", "aggregate", "distance"
}


@dataclass
class SpatialResult:
    operations: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    features: List[Dict[str, Any]]
    provenance: List[Dict[str, Any]]


class SpatialEngine:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, plan: AnalysisPlan) -> SpatialResult:
        """
        Execute all spatial_operations in the plan.
        Return SpatialResult with operations, statistics,
        features, provenance.
        Raise GeoMindError on unrecoverable failure.
        """
        if plan is None:
            raise GeoMindError(ErrorCode.INVALID_QUERY, "Analysis plan cannot be None")

        # Validate that all requested operations are supported
        for op in plan.spatial_operations:
            if op.op not in SUPPORTED_SPATIAL_OPS:
                raise GeoMindError(
                    ErrorCode.UNSUPPORTED_ANALYSIS,
                    f"Unsupported spatial operation: '{op.op}'"
                )

        # 1. Resolve geographic scope
        scope_geom, scope_geojson_dict, region_id = self._resolve_scope(plan.geographic_scope)
        scope_geojson_str = json.dumps(scope_geojson_dict)

        # 2. Execute spatial operations
        operations_results: List[Dict[str, Any]] = []
        collected_features: List[Dict[str, Any]] = []
        postgis_funcs: Set[str] = set()
        avg_distance_observed: Optional[float] = None
        area_observed_km2: Optional[float] = None

        dispatch_map = {
            "within": self._op_within,
            "dwithin": self._op_dwithin,
            "distance": self._op_distance,
            "area": self._op_area,
            "count": self._op_count,
            "aggregate": self._op_aggregate,
            "intersection": self._op_intersection,
            "buffer": self._op_buffer,
        }

        for op in plan.spatial_operations:
            handler = dispatch_map.get(op.op)
            if not handler:
                raise GeoMindError(
                    ErrorCode.UNSUPPORTED_ANALYSIS,
                    f"No handler for spatial operation: '{op.op}'"
                )

            t0 = time.perf_counter()
            try:
                op_res, feats, funcs = handler(scope_geom, scope_geojson_str)
                dur = (time.perf_counter() - t0) * 1000.0
                op_res["duration_ms"] = round(dur, 2)
                operations_results.append(op_res)
                collected_features.extend(feats)
                postgis_funcs.update(funcs)

                # Capture stats hints from ops
                if op.op == "distance" and "avg_distance_m" in op_res.get("details", {}):
                    avg_distance_observed = op_res["details"]["avg_distance_m"]
                elif op.op == "area" and "area_km2" in op_res.get("details", {}):
                    area_observed_km2 = op_res["details"]["area_km2"]

            except Exception as err:
                dur = (time.perf_counter() - t0) * 1000.0
                operations_results.append({
                    "op": op.op,
                    "status": "failed",
                    "result_count": 0,
                    "details": {"error": str(err)},
                    "duration_ms": round(dur, 2)
                })

        # 3. Build statistics dictionary
        tot_facilities = facility_count(self.db)
        by_type = facilities_by_type(self.db)

        # Determine area
        if region_id is not None:
            calc_area = region_area_km2(self.db, region_id)
        elif area_observed_km2 is not None:
            calc_area = area_observed_km2
        else:
            calc_area = self._calc_geometry_area_km2(scope_geom)

        if region_id is not None:
            in_region_cnt = facilities_in_region_count(self.db, region_id)
        else:
            in_region_cnt = len(collected_features) if collected_features else tot_facilities

        if avg_distance_observed is not None:
            calc_avg_dist = avg_distance_observed
        else:
            centroid = scope_geom.centroid
            calc_avg_dist = avg_facility_distance_to_point(self.db, centroid.x, centroid.y)

        dens = density_per_km2(in_region_cnt, calc_area)

        stats_dict = {
            "region_area_km2": round(calc_area, 4),
            "facility_count": tot_facilities,
            "facilities_by_type": by_type,
            "facilities_in_scope_count": in_region_cnt,
            "avg_distance_m": round(calc_avg_dist, 2),
            "density_per_km2": round(dens, 4),
        }

        # 4. Deduplicate features by id or geometry hash if necessary
        seen_ids = set()
        dedup_features = []
        for feat in collected_features:
            feat_id = feat.get("properties", {}).get("id")
            if feat_id:
                if feat_id not in seen_ids:
                    seen_ids.add(feat_id)
                    dedup_features.append(feat)
            else:
                dedup_features.append(feat)

        # 5. Build provenance list
        provenance_list = [
            {
                "datasets": plan.datasets,
                "postgis_functions": sorted(list(postgis_funcs)),
                "srid": DEFAULT_SRID,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]

        return SpatialResult(
            operations=operations_results,
            statistics=stats_dict,
            features=dedup_features,
            provenance=provenance_list,
        )

    def _resolve_scope(self, scope) -> tuple[shapely.geometry.base.BaseGeometry, Dict[str, Any], Optional[int]]:
        """Resolve GeographicScope into a Shapely geometry, GeoJSON dict, and optional region_id."""
        if scope is None:
            raise GeoMindError(ErrorCode.INVALID_GEOMETRY, "Geographic scope is None")

        scope_type = getattr(scope, "type", "demo_default")
        region_id = None

        if scope_type == "polygon":
            coords = getattr(scope, "coordinates", None)
            if not coords:
                raise GeoMindError(ErrorCode.INVALID_GEOMETRY, "Polygon geographic scope missing coordinates")
            try:
                if isinstance(coords, list) and len(coords) > 0:
                    if isinstance(coords[0], list) and isinstance(coords[0][0], list):
                        geom = Polygon(coords[0])
                    elif isinstance(coords[0], list) and (isinstance(coords[0][0], (int, float)) or len(coords[0]) == 2):
                        geom = Polygon(coords)
                    else:
                        geom = shape(coords)
                else:
                    geom = shape(coords)
            except Exception as e:
                raise GeoMindError(ErrorCode.INVALID_GEOMETRY, f"Failed to parse polygon coordinates: {e}")

        elif scope_type == "named_place":
            name = getattr(scope, "name", None)
            if not name:
                raise GeoMindError(ErrorCode.INVALID_GEOMETRY, "Named place geographic scope missing name")

            try:
                query = text("""
                    SELECT id, name, ST_AsGeoJSON(geom) AS geom_json
                    FROM geographic_regions
                    WHERE LOWER(name) = LOWER(:name)
                    LIMIT 1
                """)
                row = self.db.execute(query, {"name": name}).mappings().first()
                if row and row["geom_json"]:
                    region_id = row["id"]
                    geom = shape(json.loads(row["geom_json"]))
                else:
                    raise GeoMindError(ErrorCode.NO_DATA, f"Named region '{name}' not found in database")
            except GeoMindError:
                raise
            except Exception as e:
                raise GeoMindError(ErrorCode.SPATIAL_ANALYSIS_FAILED, f"Error resolving named place '{name}': {e}")

        else:
            # demo_default
            bbox_str = settings.DEMO_BBOX
            try:
                parts = [float(x.strip()) for x in bbox_str.split(",")]
                if len(parts) != 4:
                    raise ValueError(f"Invalid BBOX split: {bbox_str}")
                geom = bbox_to_polygon(parts[0], parts[1], parts[2], parts[3])
            except Exception as e:
                raise GeoMindError(ErrorCode.INVALID_GEOMETRY, f"Failed to build default demo BBOX polygon: {e}")

        if not validate_geometry(geom):
            raise GeoMindError(ErrorCode.INVALID_GEOMETRY, "Resolved scope geometry is invalid or empty")

        return geom, to_geojson_dict(geom), region_id

    def _calc_geometry_area_km2(self, geom: shapely.geometry.base.BaseGeometry) -> float:
        """Calculate approximate area in km² for WGS84 geometry using PostGIS if available, else Shapely fallback."""
        try:
            scope_json = json.dumps(to_geojson_dict(geom))
            query = text("SELECT ST_Area(ST_SetSRID(ST_GeomFromGeoJSON(:scope_json), 4326)::geography) / 1e6 AS area_km2")
            val = self.db.execute(query, {"scope_json": scope_json}).scalar()
            if val is not None:
                return float(val)
        except Exception:
            pass
        # Fallback degree-based approximation
        return float(geom.area * 111.0 * 111.0)

    # --- Operation Handlers ---

    def _op_within(self, scope_geom, scope_geojson_str) -> tuple[Dict[str, Any], List[Dict[str, Any]], List[str]]:
        query = text("""
            SELECT f.id, f.name, f.feature_type, f.category, f.source_id, f.attributes,
                   ST_AsGeoJSON(f.geom) AS geom_json
            FROM facilities f
            WHERE ST_Within(f.geom, ST_SetSRID(ST_GeomFromGeoJSON(:scope_json), 4326))
        """)
        res = self.db.execute(query, {"scope_json": scope_geojson_str}).mappings().all()

        features = []
        for row in res:
            features.append({
                "type": "Feature",
                "geometry": json.loads(row["geom_json"]),
                "properties": {
                    "id": row["id"],
                    "name": row["name"],
                    "feature_type": row["feature_type"],
                    "category": row["category"],
                    "source": "facilities",
                    "label": row["name"],
                    "confidence": 1.0,
                }
            })

        op_result = {
            "op": "within",
            "status": "ok",
            "result_count": len(features),
            "details": {"dataset": "facilities"},
        }
        return op_result, features, ["ST_Within", "ST_GeomFromGeoJSON"]

    def _op_dwithin(self, scope_geom, scope_geojson_str, distance_m: float = 5000.0) -> tuple[Dict[str, Any], List[Dict[str, Any]], List[str]]:
        query = text("""
            SELECT f.id, f.name, f.feature_type, f.category, f.source_id, f.attributes,
                   ST_Distance(f.geom::geography, ST_SetSRID(ST_GeomFromGeoJSON(:scope_json), 4326)::geography) AS distance_m,
                   ST_AsGeoJSON(f.geom) AS geom_json
            FROM facilities f
            WHERE ST_DWithin(f.geom::geography, ST_SetSRID(ST_GeomFromGeoJSON(:scope_json), 4326)::geography, :distance_m)
            ORDER BY distance_m
        """)
        res = self.db.execute(query, {"scope_json": scope_geojson_str, "distance_m": distance_m}).mappings().all()

        features = []
        for row in res:
            features.append({
                "type": "Feature",
                "geometry": json.loads(row["geom_json"]),
                "properties": {
                    "id": row["id"],
                    "name": row["name"],
                    "feature_type": row["feature_type"],
                    "category": row["category"],
                    "distance_m": float(row["distance_m"]),
                    "source": "facilities",
                    "label": row["name"],
                    "confidence": 1.0,
                }
            })

        op_result = {
            "op": "dwithin",
            "status": "ok",
            "result_count": len(features),
            "details": {"distance_m": distance_m, "dataset": "facilities"},
        }
        return op_result, features, ["ST_DWithin", "ST_Distance", "ST_GeomFromGeoJSON"]

    def _op_distance(self, scope_geom, scope_geojson_str) -> tuple[Dict[str, Any], List[Dict[str, Any]], List[str]]:
        query = text("""
            SELECT f.id, f.name, f.feature_type, f.category,
                   ST_Distance(f.geom::geography, ST_Centroid(ST_SetSRID(ST_GeomFromGeoJSON(:scope_json), 4326))::geography) AS distance_m,
                   ST_AsGeoJSON(f.geom) AS geom_json
            FROM facilities f
            ORDER BY distance_m
        """)
        res = self.db.execute(query, {"scope_json": scope_geojson_str}).mappings().all()

        distances = [float(r["distance_m"]) for r in res]
        avg_dist = float(sum(distances) / len(distances)) if distances else 0.0
        min_dist = min(distances) if distances else 0.0
        max_dist = max(distances) if distances else 0.0

        features = []
        for row in res:
            features.append({
                "type": "Feature",
                "geometry": json.loads(row["geom_json"]),
                "properties": {
                    "id": row["id"],
                    "name": row["name"],
                    "feature_type": row["feature_type"],
                    "distance_m": float(row["distance_m"]),
                    "source": "facilities",
                    "label": row["name"],
                    "confidence": 1.0,
                }
            })

        op_result = {
            "op": "distance",
            "status": "ok",
            "result_count": len(features),
            "details": {
                "avg_distance_m": round(avg_dist, 2),
                "min_distance_m": round(min_dist, 2),
                "max_distance_m": round(max_dist, 2),
            },
        }
        return op_result, features, ["ST_Distance", "ST_Centroid", "ST_GeomFromGeoJSON"]

    def _op_area(self, scope_geom, scope_geojson_str) -> tuple[Dict[str, Any], List[Dict[str, Any]], List[str]]:
        query = text("""
            SELECT ST_Area(ST_SetSRID(ST_GeomFromGeoJSON(:scope_json), 4326)::geography) / 1e6 AS area_km2
        """)
        val = self.db.execute(query, {"scope_json": scope_geojson_str}).scalar()
        area_km2 = float(val) if val is not None else self._calc_geometry_area_km2(scope_geom)

        op_result = {
            "op": "area",
            "status": "ok",
            "result_count": 1,
            "details": {"area_km2": round(area_km2, 4)},
        }
        return op_result, [], ["ST_Area", "ST_GeomFromGeoJSON"]

    def _op_count(self, scope_geom, scope_geojson_str) -> tuple[Dict[str, Any], List[Dict[str, Any]], List[str]]:
        query = text("""
            SELECT COUNT(*) AS count
            FROM facilities f
            WHERE ST_Within(f.geom, ST_SetSRID(ST_GeomFromGeoJSON(:scope_json), 4326))
        """)
        cnt = self.db.execute(query, {"scope_json": scope_geojson_str}).scalar()
        cnt_val = int(cnt) if cnt is not None else 0

        op_result = {
            "op": "count",
            "status": "ok",
            "result_count": cnt_val,
            "details": {"count": cnt_val},
        }
        return op_result, [], ["ST_Within", "COUNT", "ST_GeomFromGeoJSON"]

    def _op_aggregate(self, scope_geom, scope_geojson_str) -> tuple[Dict[str, Any], List[Dict[str, Any]], List[str]]:
        query = text("""
            SELECT f.feature_type, COUNT(*) AS count
            FROM facilities f
            WHERE ST_Within(f.geom, ST_SetSRID(ST_GeomFromGeoJSON(:scope_json), 4326))
            GROUP BY f.feature_type
        """)
        res = self.db.execute(query, {"scope_json": scope_geojson_str}).mappings().all()
        by_type = {r["feature_type"]: int(r["count"]) for r in res}

        if not by_type:
            # Fallback aggregate all facilities if none within scope
            fallback_query = text("SELECT feature_type, COUNT(*) AS count FROM facilities GROUP BY feature_type")
            res_fb = self.db.execute(fallback_query).mappings().all()
            by_type = {r["feature_type"]: int(r["count"]) for r in res_fb}

        op_result = {
            "op": "aggregate",
            "status": "ok",
            "result_count": len(by_type),
            "details": {"facilities_by_type": by_type},
        }
        return op_result, [], ["ST_Within", "GROUP BY", "ST_GeomFromGeoJSON"]

    def _op_intersection(self, scope_geom, scope_geojson_str) -> tuple[Dict[str, Any], List[Dict[str, Any]], List[str]]:
        query = text("""
            SELECT r.id, r.name, r.region_type,
                   ST_AsGeoJSON(ST_Intersection(r.geom, ST_SetSRID(ST_GeomFromGeoJSON(:scope_json), 4326))) AS geom_json
            FROM geographic_regions r
            WHERE ST_Intersects(r.geom, ST_SetSRID(ST_GeomFromGeoJSON(:scope_json), 4326))
        """)
        res = self.db.execute(query, {"scope_json": scope_geojson_str}).mappings().all()

        features = []
        for row in res:
            if row["geom_json"]:
                features.append({
                    "type": "Feature",
                    "geometry": json.loads(row["geom_json"]),
                    "properties": {
                        "region_id": row["id"],
                        "name": row["name"],
                        "region_type": row["region_type"],
                        "feature_type": "intersection_region",
                        "source": "geographic_regions",
                        "label": f"Intersection with {row['name']}",
                        "confidence": 1.0,
                    }
                })

        op_result = {
            "op": "intersection",
            "status": "ok",
            "result_count": len(features),
            "details": {"intersection_count": len(features)},
        }
        return op_result, features, ["ST_Intersection", "ST_Intersects", "ST_GeomFromGeoJSON"]

    def _op_buffer(self, scope_geom, scope_geojson_str, buffer_m: float = 1000.0) -> tuple[Dict[str, Any], List[Dict[str, Any]], List[str]]:
        query = text("""
            SELECT ST_AsGeoJSON(ST_Buffer(ST_SetSRID(ST_GeomFromGeoJSON(:scope_json), 4326)::geography, :buffer_m)::geometry) AS geom_json
        """)
        val = self.db.execute(query, {"scope_json": scope_geojson_str, "buffer_m": buffer_m}).scalar()

        features = []
        if val:
            features.append({
                "type": "Feature",
                "geometry": json.loads(val),
                "properties": {
                    "feature_type": "buffer_zone",
                    "source": "spatial_engine",
                    "buffer_m": buffer_m,
                    "label": f"Buffer zone ({buffer_m}m)",
                    "confidence": 1.0,
                }
            })

        op_result = {
            "op": "buffer",
            "status": "ok",
            "result_count": len(features),
            "details": {"buffer_m": buffer_m},
        }
        return op_result, features, ["ST_Buffer", "ST_GeomFromGeoJSON"]
