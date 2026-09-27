from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql://geomind:geomind@localhost:5432/geomind"
    POSTGIS_ENABLED: bool = True
    AI_PROVIDER: str = "stub"
    AI_MODEL: str = "stub-model"
    AI_API_KEY: Optional[str] = None
    AI_TIMEOUT_SECONDS: int = 20
    AI_MAX_RETRIES: int = 2
    AI_ENABLED: bool = True
    DEMO_BBOX: str = "-1.5,36.5,-1.1,37.0"
    DEMO_UTM_EPSG: int = 32737
    LOG_LEVEL: str = "INFO"
    MAX_QUERY_LENGTH: int = 500
    MAX_POLYGON_VERTICES: int = 1000

settings = Settings()
