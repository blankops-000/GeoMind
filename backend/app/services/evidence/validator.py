from __future__ import annotations
from uuid import UUID
from typing import Any
from app.schemas.evidence import EvidencePackage, EvidenceItem
from app.core.errors import GeoMindError, ErrorCode

VALID_GEOJSON_TYPES = {
    "Point",
    "MultiPoint",
    "LineString",
    "MultiLineString",
    "Polygon",
    "MultiPolygon",
    "GeometryCollection",
}

class EvidenceValidator:
    """
    Validator to verify EvidencePackage integrity before reaching AI interpretation.
    """

    def validate(self, package: EvidencePackage) -> None:
        """
        Raise GeoMindError if the package is invalid.
        """
        analysis_id_str = str(getattr(package, "analysis_id", ""))

        # Rule 1: analysis_id must be a UUID
        if not isinstance(package.analysis_id, UUID):
            try:
                UUID(str(package.analysis_id))
            except Exception as exc:
                raise GeoMindError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message=f"Evidence package failed validation: Invalid analysis_id UUID ({exc})",
                    details={"package_analysis_id": analysis_id_str},
                )

        # Rule 2: package.area must be a non-empty string
        if not package.area or not isinstance(package.area, str) or not package.area.strip():
            raise GeoMindError(
                code=ErrorCode.INTERNAL_ERROR,
                message="Evidence package failed validation: area must be a non-empty string",
                details={"package_analysis_id": analysis_id_str},
            )

        # Rule 3: package.evidence_items must be non-empty
        if not package.evidence_items or not isinstance(package.evidence_items, list):
            raise GeoMindError(
                code=ErrorCode.INTERNAL_ERROR,
                message="Evidence package failed validation: evidence_items list cannot be empty",
                details={"package_analysis_id": analysis_id_str},
            )

        # Rule 4: Every EvidenceItem must have non-empty description and source
        for idx, item in enumerate(package.evidence_items):
            if not item.description or not isinstance(item.description, str) or not item.description.strip():
                raise GeoMindError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message=f"Evidence package failed validation: EvidenceItem[{idx}] missing description",
                    details={"package_analysis_id": analysis_id_str},
                )
            if not item.source or not isinstance(item.source, str) or not item.source.strip():
                raise GeoMindError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message=f"Evidence package failed validation: EvidenceItem[{idx}] missing source",
                    details={"package_analysis_id": analysis_id_str},
                )

            # Rule 5: Numeric value without unit metadata check
            if item.value is not None and item.unit is None and isinstance(item.value, (int, float)):
                if item.metadata is None:
                    item.metadata = {}
                item.metadata.setdefault("unit_inferred", True)

            # Rule 6: Geometry validation if present
            if item.geometry is not None:
                if not isinstance(item.geometry, dict):
                    raise GeoMindError(
                        code=ErrorCode.INTERNAL_ERROR,
                        message=f"Evidence package failed validation: EvidenceItem[{idx}] geometry must be a dict",
                        details={"package_analysis_id": analysis_id_str},
                    )
                geom_type = item.geometry.get("type")
                coords = item.geometry.get("coordinates")
                if not geom_type or coords is None:
                    raise GeoMindError(
                        code=ErrorCode.INTERNAL_ERROR,
                        message=f"Evidence package failed validation: EvidenceItem[{idx}] geometry missing type or coordinates",
                        details={"package_analysis_id": analysis_id_str},
                    )
                if geom_type not in VALID_GEOJSON_TYPES:
                    raise GeoMindError(
                        code=ErrorCode.INTERNAL_ERROR,
                        message=f"Evidence package failed validation: EvidenceItem[{idx}] invalid GeoJSON geometry type '{geom_type}'",
                        details={"package_analysis_id": analysis_id_str},
                    )

        # Rule 7: package.confidence["overall"] between 0 and 1
        if isinstance(package.confidence, dict) and "overall" in package.confidence:
            overall = package.confidence["overall"]
            if overall is not None:
                if not isinstance(overall, (int, float)) or not (0.0 <= overall <= 1.0):
                    raise GeoMindError(
                        code=ErrorCode.INTERNAL_ERROR,
                        message=f"Evidence package failed validation: overall confidence {overall} must be between 0 and 1",
                        details={"package_analysis_id": analysis_id_str},
                    )
