from __future__ import annotations
from typing import Dict, Any, List
import numpy as np
from pyproj import Transformer
from shapely.geometry import Polygon, shape, mapping
from shapely.ops import transform
from app.schemas.vision import VisionInput, VisionResult
from app.services.vision.georeference import bbox_to_geographic, mask_to_polygons
from app.utils.geometry import validate_geometry, repair_geometry
from app.core.config import settings

def _calculate_area_km2(geom_dict: dict) -> float:
    """Calculate area in square kilometers for an EPSG:4326 geometry."""
    try:
        poly = shape(geom_dict)
        if not poly.is_valid:
            poly = repair_geometry(poly)
        if poly is None or poly.is_empty:
            return 0.0

        # Transform to UTM EPSG:32737 (or DEMO_UTM_EPSG) for accurate area in meters
        utm_epsg = getattr(settings, "DEMO_UTM_EPSG", 32737)
        transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True)
        utm_poly = transform(transformer.transform, poly)
        return float(utm_poly.area / 1_000_000.0)
    except Exception:
        return 0.0

class SegmentationProcessor:
    name = "segmentation"
    version = "0.1.0"

    def process(self, input: VisionInput, task: str, params: dict) -> VisionResult:
        """
        Execute segmentation task.
        In MVP / demo mode, produces georeferenced segmentation polygons over the analysis region.
        """
        merged_params = {**input.parameters, **params}
        target_feature = merged_params.get("target_feature", "vegetation")

        # Demo / Synthetic path when imagery is a mock ref or file not found
        affine = merged_params.get("affine_transform")
        src_crs = merged_params.get("src_crs", "EPSG:32737")

        regions: List[dict] = []
        
        if affine is not None:
            # Synthetic 100x100 mask
            mask = np.zeros((100, 100), dtype=bool)
            mask[20:60, 20:60] = True
            regions = mask_to_polygons(mask, affine, src_crs=src_crs, dst_crs="EPSG:4326")
        
        if not regions:
            # Fallback to demo bbox georeferenced region in Nairobi area
            demo_poly_dict = bbox_to_geographic(
                (20.0, 20.0, 60.0, 60.0),
                (0.001, 0.0, 36.80, 0.0, -0.001, -1.28),
                src_crs="EPSG:4326",
                dst_crs="EPSG:4326"
            )
            if demo_poly_dict:
                regions = [demo_poly_dict]

        total_area_km2 = sum(_calculate_area_km2(r) for r in regions)

        return VisionResult(
            task_type=task,
            model_name="SegmentationProcessor",
            model_version=self.version,
            source_imagery_id=input.imagery_ref,
            label=f"segmentation_{target_feature}",
            confidence=0.88,
            regions=regions,
            area_km2=round(total_area_km2, 4),
            count=len(regions),
            statistics={
                "segmentation_area_km2": round(total_area_km2, 4),
                "target_feature": target_feature,
                "region_count": len(regions),
            },
            processing_metadata={
                "processor": self.name,
                "version": self.version,
                "target_feature": target_feature,
            },
            quality_flags=["DEMO_SYNTHETIC_INFERENCE"],
        )
