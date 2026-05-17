import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app():
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://campusconnect:campusconnect@localhost:5432/campusconnect_test")
    os.environ.setdefault("DATABASE_URL_SYNC", "postgresql+psycopg://campusconnect:campusconnect@localhost:5432/campusconnect_test")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
    os.environ.setdefault("CELERY_BROKER_URL", "memory://")
    os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")
    os.environ.setdefault("APP_ENV", "test")
    os.environ.setdefault("AUTH_SECRET", "test-secret-not-for-prod")
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture()
def client(app):
    return TestClient(app)
