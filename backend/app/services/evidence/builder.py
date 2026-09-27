from __future__ import annotations
from typing import Optional, Any
from uuid import UUID
from app.schemas.evidence import EvidenceItem, EvidencePackage

def build_evidence_package(
    analysis_id: UUID,
    area: str,
    datasets: list[str],
    spatial_result: dict[str, Any],
    vision_results: Optional[list[dict[str, Any]]],
    statistics: dict[str, Any],
    provenance: list[dict[str, Any]],
) -> EvidencePackage:
    """
    Assemble an EvidencePackage from all measured sources.
    Every numeric claim becomes an EvidenceItem with a source.
    """
    items: list[EvidenceItem] = []
    limitations: list[str] = []
    quality_flags: list[str] = []
    prov_list: list[dict[str, Any]] = list(provenance or [])

    # 1. Dataset Evidence Items
    for ds in (datasets or []):
        items.append(
            EvidenceItem(
                evidence_type="dataset",
                description=f"Dataset loaded: {ds}",
                value=ds,
                source=ds,
                confidence=1.0,
            )
        )
        if "synthetic" in str(ds).lower():
            if "Synthetic demo data" not in limitations:
                limitations.append("Synthetic demo data")

    # 2. Spatial Results Evidence Items
    operations = spatial_result.get("operations", []) if isinstance(spatial_result, dict) else []
    if operations:
        for op in operations:
            if isinstance(op, dict):
                status = op.get("status", "ok")
                if status in (None, "ok", "success"):
                    op_name = op.get("op", op.get("operation", "spatial_operation"))
                    count = op.get("result_count", op.get("count", len(op.get("features", []))))
                    duration = op.get("duration_ms", 0)
                    items.append(
                        EvidenceItem(
                            evidence_type="spatial",
                            description=f"{op_name} produced {count} results",
                            value=count,
                            source="PostGIS",
                            confidence=0.9,
                            metadata={"op": op_name, "duration_ms": duration},
                        )
                    )
    elif isinstance(spatial_result, dict) and ("features" in spatial_result or "count" in spatial_result):
        count = spatial_result.get("count", len(spatial_result.get("features", [])))
        items.append(
            EvidenceItem(
                evidence_type="spatial",
                description=f"Spatial analysis produced {count} results",
                value=count,
                source="PostGIS",
                confidence=0.9,
            )
        )

    # 3. Statistics Evidence Items
    if isinstance(statistics, dict):
        for key, value in statistics.items():
            desc = f"{key.replace('_', ' ')} = {value}"
            items.append(
                EvidenceItem(
                    evidence_type="statistic",
                    description=desc,
                    value=value,
                    source="PostGIS statistics",
                    confidence=0.9,
                )
            )

    # 4. Computer Vision Results Evidence Items
    cv_dict: Optional[dict[str, Any]] = None
    if vision_results:
        if isinstance(vision_results, list):
            cv_dict = {"results": vision_results}
            for vr in vision_results:
                if isinstance(vr, dict):
                    label = vr.get("label", vr.get("target_feature", "detection"))
                    area_km2 = vr.get("area_km2", vr.get("value", 0.0))
                    conf = vr.get("confidence", 0.8)
                    m_name = vr.get("model_name", "vision_model")
                    m_ver = vr.get("model_version", "1.0")
                    geom = vr.get("geometry")
                    if not geom and vr.get("regions"):
                        geom = vr["regions"][0].get("geometry")

                    items.append(
                        EvidenceItem(
                            evidence_type="cv",
                            description=f"Detected {label} over {area_km2} km²",
                            value=area_km2,
                            unit="km²",
                            geometry=geom,
                            source=f"{m_name} v{m_ver}",
                            confidence=conf,
                        )
                    )
                    # Quality flags from CV
                    for qf in vr.get("quality_flags", []):
                        if qf not in quality_flags:
                            quality_flags.append(qf)
                    
                    # Provenance from CV
                    prov_list.append({
                        "type": "cv_model",
                        "model_name": m_name,
                        "model_version": m_ver,
                        "confidence": conf,
                    })
        elif isinstance(vision_results, dict):
            cv_dict = vision_results

    # 5. Check numeric value sources & unverified rule
    for item in items:
        if isinstance(item.value, (int, float)) and (not item.source or not item.source.strip()):
            if "unverified" not in limitations:
                limitations.append("unverified")
            item.confidence = None

    # Check for synthetic in provenance
    for p in prov_list:
        if "synthetic" in str(p).lower() and "Synthetic demo data" not in limitations:
            limitations.append("Synthetic demo data")

    # Standard limitation mandatory requirement
    standard_limitation = "Confidence reflects model output, not analytical truth"
    if standard_limitation not in limitations:
        limitations.append(standard_limitation)

    # 6. Overall Confidence Calculation
    valid_confidences = [item.confidence for item in items if item.confidence is not None]
    overall_confidence = (
        sum(valid_confidences) / len(valid_confidences)
        if valid_confidences
        else 0.5
    )

    # Geographic features extraction
    geo_features = spatial_result.get("features", []) if isinstance(spatial_result, dict) else []

    return EvidencePackage(
        analysis_id=analysis_id,
        area=area,
        datasets=datasets or [],
        spatial_results=spatial_result or {},
        computer_vision=cv_dict,
        statistics=statistics or {},
        geographic_features=geo_features,
        evidence_items=items,
        confidence={"overall": overall_confidence},
        provenance=prov_list,
        limitations=limitations,
        quality_flags=quality_flags,
    )
