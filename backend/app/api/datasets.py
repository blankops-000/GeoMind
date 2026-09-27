from fastapi import APIRouter, Depends
from app.api.deps import dataset_repo

router = APIRouter()


@router.get("")
@router.get("/")
def list_datasets(repo=Depends(dataset_repo)):
    rows = repo.list_all()
    return {
        "datasets": [
            {
                "name": r.get("name"),
                "source": r.get("source"),
                "license": r.get("license"),
                "coverage": r.get("coverage"),
            }
            for r in rows
        ]
    }
