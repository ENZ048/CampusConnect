from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None,  # rely on the environment, not a file inside the package
        case_sensitive=True,
        extra="ignore",
    )

    APP_ENV: str = Field(default="local")
    DATABASE_URL: str
    DATABASE_URL_SYNC: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    AUTH_SECRET: str
    API_BASE_URL: str = "http://localhost:8000"
    SENTRY_DSN_API: str | None = None
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None
    OTEL_SERVICE_NAME_API: str = "campusconnect-api"


@lru_cache
def get_settings() -> Settings:
    return Settings()
