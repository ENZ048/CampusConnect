# CampusConnect API

FastAPI service. Also the Python package source for the Celery worker and beat.

## Develop

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

## Test

```bash
uv run pytest -xvs
```

## Migrate

```bash
uv run alembic upgrade head
```
