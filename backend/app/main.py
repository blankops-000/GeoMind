from fastapi import FastAPI
from app.api import health, query, analysis, datasets
from app.api.errors import register_error_handlers
from app.core.logging import get_logger

logger = get_logger("app.main")

app = FastAPI(title="GeoMind AI", docs_url="/docs")

app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(query.router, prefix="/api/v1/query", tags=["query"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["datasets"])

register_error_handlers(app)

@app.on_event("startup")
async def startup_event():
    logger.info("GeoMind AI application initialized")
