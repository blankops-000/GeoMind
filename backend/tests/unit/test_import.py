def test_app_imports():
    from app.main import app
    assert app is not None

def test_schemas_import():
    from app.schemas.query import QueryIntent
    from app.schemas.plan import AnalysisPlan
    from app.schemas.vision import VisionResult
    from app.schemas.evidence import EvidencePackage
    from app.schemas.result import AnalysisResult
    from app.schemas.geojson import FeatureCollection
    assert QueryIntent is not None
