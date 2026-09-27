import pytest
from uuid import uuid4
from app.schemas.evidence import EvidencePackage, EvidenceItem
from app.services.evidence.validator import EvidenceValidator
from app.core.errors import GeoMindError, ErrorCode

@pytest.fixture
def valid_package():
    return EvidencePackage(
        analysis_id=uuid4(),
        area="Nairobi",
        datasets=["facilities"],
        evidence_items=[
            EvidenceItem(
                evidence_type="spatial",
                description="facilities within region count = 10",
                value=10,
                source="PostGIS",
                confidence=0.9,
            )
        ],
        confidence={"overall": 0.9},
        limitations=["Confidence reflects model output"],
    )

def test_evidence_validator_valid_package(valid_package):
    validator = EvidenceValidator()
    validator.validate(valid_package)  # Should not raise

def test_evidence_validator_empty_evidence_items_raises(valid_package):
    valid_package.evidence_items = []
    validator = EvidenceValidator()
    with pytest.raises(GeoMindError) as exc_info:
        validator.validate(valid_package)
    assert exc_info.value.code == ErrorCode.INTERNAL_ERROR
    assert "evidence_items list cannot be empty" in exc_info.value.message

def test_evidence_validator_missing_source_raises(valid_package):
    valid_package.evidence_items[0].source = ""
    validator = EvidenceValidator()
    with pytest.raises(GeoMindError) as exc_info:
        validator.validate(valid_package)
    assert exc_info.value.code == ErrorCode.INTERNAL_ERROR
    assert "missing source" in exc_info.value.message

def test_evidence_validator_invalid_geometry_raises(valid_package):
    valid_package.evidence_items[0].geometry = {
        "type": "InvalidShapeType",
        "coordinates": [0, 0]
    }
    validator = EvidenceValidator()
    with pytest.raises(GeoMindError) as exc_info:
        validator.validate(valid_package)
    assert exc_info.value.code == ErrorCode.INTERNAL_ERROR
    assert "invalid GeoJSON geometry type" in exc_info.value.message

def test_evidence_validator_invalid_overall_confidence_raises(valid_package):
    valid_package.confidence["overall"] = 1.5
    validator = EvidenceValidator()
    with pytest.raises(GeoMindError) as exc_info:
        validator.validate(valid_package)
    assert exc_info.value.code == ErrorCode.INTERNAL_ERROR
    assert "overall confidence 1.5 must be between 0 and 1" in exc_info.value.message
