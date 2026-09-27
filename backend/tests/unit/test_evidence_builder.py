import pytest
from uuid import uuid4
from app.services.evidence.builder import build_evidence_package
from app.schemas.evidence import EvidencePackage

def test_build_evidence_package_basic():
    analysis_id = uuid4()
    area = "Nairobi"
    datasets = ["facilities", "geographic_regions"]
    spatial_result = {
        "operations": [
            {
                "op": "within",
                "status": "ok",
                "result_count": 15,
                "duration_ms": 120,
            }
        ],
        "features": [{"id": 1, "type": "Feature"}],
    }
    stats = {"facility_count": 15, "region_area_km2": 696.0}
    provenance = [{"step": "spatial_query"}]

    package = build_evidence_package(
        analysis_id=analysis_id,
        area=area,
        datasets=datasets,
        spatial_result=spatial_result,
        vision_results=None,
        statistics=stats,
        provenance=provenance,
    )

    assert isinstance(package, EvidencePackage)
    assert package.analysis_id == analysis_id
    assert package.area == "Nairobi"
    assert len(package.evidence_items) > 0

    # Verify every item has a non-empty source
    for item in package.evidence_items:
        assert item.source is not None
        assert len(item.source.strip()) > 0

    # Verify confidence
    overall_conf = package.confidence.get("overall")
    assert overall_conf is not None
    assert 0.0 <= overall_conf <= 1.0

    # Verify mandatory limitations note
    assert any("Confidence reflects model output" in lim for lim in package.limitations)

def test_build_evidence_package_with_cv_and_synthetic():
    analysis_id = uuid4()
    area = "Kiambu"
    datasets = ["synthetic_landuse"]
    spatial_result = {"operations": []}
    stats = {"built_up_km2": 12.4}
    vision_results = [
        {
            "label": "built_up",
            "area_km2": 12.4,
            "confidence": 0.85,
            "model_name": "sentinel_unet",
            "model_version": "2.1",
            "quality_flags": ["cloud_cover_low"],
        }
    ]
    provenance = []

    package = build_evidence_package(
        analysis_id=analysis_id,
        area=area,
        datasets=datasets,
        spatial_result=spatial_result,
        vision_results=vision_results,
        statistics=stats,
        provenance=provenance,
    )

    assert package.computer_vision is not None
    assert "Synthetic demo data" in package.limitations
    assert "cloud_cover_low" in package.quality_flags

    cv_items = [item for item in package.evidence_items if item.evidence_type == "cv"]
    assert len(cv_items) == 1
    assert cv_items[0].source == "sentinel_unet v2.1"
    assert cv_items[0].unit == "km²"
