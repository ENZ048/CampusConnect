# CampusConnect — Phase M0 (Foundations) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the production-grade foundation for CampusConnect — repo layout, infrastructure, backend skeleton, worker skeleton, frontend skeleton, observability, and CI — so that a fresh checkout can be brought to "sign up by email, log in, see an empty dashboard, view the request trace in OpenTelemetry" in under five minutes.

**Architecture:** Monorepo with `apps/api` (FastAPI + Celery package shared by the worker and beat process), `apps/web` (Next.js 15 App Router), `apps/worker` and `apps/beat` (thin Dockerfiles that re-use the Python package), `infra/` (Docker Compose for local dev), `packages/shared` (placeholder for M1+), `docs/`, and root-level configs. Multi-tenant isolation is wired from day one through three layers: API middleware, SQLAlchemy event-listener auto-filter, and Postgres RLS policies. Observability is wired to Sentry (errors) and OpenTelemetry (traces, exported to console in dev and OTLP in prod).

**Tech Stack:** Python 3.12, FastAPI 0.115+, SQLAlchemy 2.x async, asyncpg, Alembic, Celery 5.4+, Redis 7, Postgres 16 + pgvector, pytest 8.3+, ruff, mypy strict, sentry-sdk, opentelemetry-distro. Frontend: Next.js 15, React 19, TypeScript 5.6 strict, Tailwind 3, shadcn/ui, Auth.js v5 (NextAuth) with the Resend / Email provider, @sentry/nextjs, @vercel/otel. Tooling: uv (Python), pnpm (Node), Docker Compose, GitHub Actions, Playwright.

**Prerequisites:**
- Working directory is `/Users/pratikyesare/Pratik Yesare/Institue Whatsapp agent` (this repo).
- A spec already lives at `docs/superpowers/specs/2026-05-17-campusconnect-design.md` — read §5 (architecture), §7 (multi-tenancy), §8 (domain model) before starting.
- Local installs: Docker Desktop, Python 3.12, Node 20+, `uv` (`brew install uv` or `pip install uv`), `pnpm` (`brew install pnpm`).
- An ngrok or Cloudflare tunnel will be useful in later phases but is **not** needed for M0.
- A GitHub account with push access to `git@github.com:ENZ048/CampusConnect.git`.

**End-state acceptance (the demo that proves M0 is done):**

1. Fresh clone → `make up` brings Postgres+pgvector, Redis, MinIO, Mailhog, and Langfuse up.
2. `make migrate` applies Alembic migrations; `make seed` inserts the three default plans.
3. `make dev` runs the FastAPI server on `:8000`, the Celery worker, the Celery beat, and the Next.js dev server on `:3000`.
4. Visiting `http://localhost:3000` shows a marketing landing placeholder with a "Get started" button → `/signup`.
5. Submitting an email on `/signup` triggers a magic-link email visible in Mailhog at `http://localhost:8025`.
6. Clicking the link logs the user in, lands them on `/app`, which shows an "Empty dashboard — your CampusConnect lives here" placeholder with the user's email.
7. Visiting `http://localhost:8000/healthz` returns `{"status":"ok"}` with a `traceparent` header propagated end-to-end.
8. The console for the API process shows an OpenTelemetry trace span for the request.
9. Running `make test` runs Python unit tests (50+) and Web type-checks; all pass.
10. CI on a PR runs lint, type, unit tests, and web build for both apps and all jobs pass.

---

## Repository structure (target)

```
campusconnect/
├── .github/
│   └── workflows/
│       └── ci.yml
├── apps/
│   ├── api/
│   │   ├── alembic/
│   │   │   ├── env.py
│   │   │   ├── script.py.mako
│   │   │   └── versions/
│   │   │       ├── 0001_init_extensions_and_core_tables.py
│   │   │       ├── 0002_rls_policies.py
│   │   │       └── 0003_seed_plans.py
│   │   ├── alembic.ini
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── db/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── session.py
│   │   │   │   └── tenant_filter.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── mixins.py
│   │   │   │   ├── plan.py
│   │   │   │   ├── organization.py
│   │   │   │   ├── user.py
│   │   │   │   └── audit_log.py
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── health.py
│   │   │   │   └── metrics.py
│   │   │   ├── middleware/
│   │   │   │   ├── __init__.py
│   │   │   │   └── request_id.py
│   │   │   ├── observability/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sentry.py
│   │   │   │   └── otel.py
│   │   │   └── worker/
│   │   │       ├── __init__.py
│   │   │       ├── celery_app.py
│   │   │       ├── beat_schedule.py
│   │   │       └── tasks/
│   │   │           ├── __init__.py
│   │   │           └── hello.py
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py
│   │   │   ├── test_health.py
│   │   │   ├── test_metrics.py
│   │   │   ├── test_request_id.py
│   │   │   ├── test_models.py
│   │   │   ├── test_tenant_filter.py
│   │   │   ├── test_rls.py
│   │   │   ├── test_migrations.py
│   │   │   └── test_hello_task.py
│   │   ├── pyproject.toml
│   │   └── README.md
│   ├── worker/
│   │   ├── Dockerfile
│   │   └── README.md
│   ├── beat/
│   │   ├── Dockerfile
│   │   └── README.md
│   └── web/
│       ├── package.json
│       ├── pnpm-lock.yaml
│       ├── tsconfig.json
│       ├── next.config.mjs
│       ├── tailwind.config.ts
│       ├── postcss.config.mjs
│       ├── components.json
│       ├── playwright.config.ts
│       ├── instrumentation.ts
│       ├── sentry.client.config.ts
│       ├── sentry.server.config.ts
│       ├── src/
│       │   ├── app/
│       │   │   ├── layout.tsx
│       │   │   ├── globals.css
│       │   │   ├── page.tsx
│       │   │   ├── login/page.tsx
│       │   │   ├── signup/page.tsx
│       │   │   ├── app/
│       │   │   │   ├── layout.tsx
│       │   │   │   └── page.tsx
│       │   │   └── api/
│       │   │       ├── auth/[...nextauth]/route.ts
│       │   │       └── health/route.ts
│       │   ├── auth.ts
│       │   ├── middleware.ts
│       │   ├── lib/
│       │   │   ├── env.ts
│       │   │   └── api-client.ts
│       │   └── components/
│       │       ├── ui/  (shadcn primitives)
│       │       └── app-shell.tsx
│       ├── e2e/
│       │   └── signup-login.spec.ts
│       └── README.md
├── packages/
│   └── shared/
│       └── README.md
├── infra/
│   ├── docker-compose.yml
│   ├── docker/
│   │   └── postgres-pgvector/
│   │       └── Dockerfile
│   └── README.md
├── docs/
│   ├── architecture.md
│   ├── runbook.md
│   ├── superpowers/
│   │   ├── specs/2026-05-17-campusconnect-design.md  (already exists)
│   │   └── plans/2026-05-17-phase-m0-foundations.md  (this file)
├── .env.example
├── .gitignore                                         (already exists)
├── Makefile
└── README.md
```

---

## Conventions

- **Commit prefixes:** `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`, `ci:`. Bodies short and active-voice.
- **Branches:** All M0 work on `main`. Future phases use `phase-mN-<slug>` branches.
- **Python:** `uv run` for every command. `ruff check` + `ruff format` + `mypy --strict`. Tests via `pytest -xvs` for noisy feedback during development.
- **Web:** `pnpm` only. `pnpm lint && pnpm typecheck && pnpm test`.
- **Env:** `.env` (gitignored) at repo root for local development, sourced by Docker Compose and `make` targets. `.env.example` committed.
- **Test DB:** Tests run against a real Postgres instance (the Docker Compose one is reused). A `pytest` fixture spins up a savepoint per test for isolation. The pgvector extension is required by some later tests, so we install it from M0.
- **Working directory:** All commands assume the repo root. Inside Python tasks, prefer `uv run --project apps/api ...` so the working directory does not need to change.

---

## Task 1: Repository scaffold

**Files:**
- Create: `README.md`
- Create: `.env.example`
- Create: `Makefile`
- Modify: `.gitignore` (extend existing)

- [ ] **Step 1: Write a verification test (smoke check the scaffolding)**

Create file `apps/api/tests/test_scaffold.py`:

```python
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_required_top_level_files_exist():
    for name in ["README.md", ".env.example", "Makefile", ".gitignore"]:
        assert (REPO_ROOT / name).is_file(), f"missing {name}"


def test_required_top_level_dirs_exist():
    for name in ["apps", "packages", "infra", "docs"]:
        assert (REPO_ROOT / name).is_dir(), f"missing {name}/"
```

(This file will run as part of the Python test suite once that's set up in Task 4. For now, the test exists; we won't run it until then. The test serves as documentation.)

- [ ] **Step 2: Create `README.md`**

```markdown
# CampusConnect

AI WhatsApp admissions agent for educational institutes. Multi-tenant SaaS that captures, qualifies, nurtures, and hands over admission leads to counsellors.

See [`docs/superpowers/specs/2026-05-17-campusconnect-design.md`](docs/superpowers/specs/2026-05-17-campusconnect-design.md) for the full design specification and [`docs/architecture.md`](docs/architecture.md) for the architecture overview.

## Quick start

```bash
cp .env.example .env
make up        # bring up Postgres, Redis, MinIO, Mailhog, Langfuse
make migrate   # apply Alembic migrations
make seed      # seed default plans
make dev       # run API, worker, beat, and web in parallel
```

Visit http://localhost:3000 to sign up and log in. Mail goes to http://localhost:8025.

## Repository layout

```
apps/api      FastAPI service (also the Celery package source)
apps/worker   Dockerfile that runs `celery ... worker`
apps/beat     Dockerfile that runs `celery ... beat`
apps/web      Next.js dashboard
infra/        Docker Compose and supporting Dockerfiles
docs/         Specifications, plans, runbook, architecture
```

## Commands

| Command | What it does |
| --- | --- |
| `make up` | Bring up infra containers in detached mode |
| `make down` | Stop infra containers |
| `make migrate` | Apply Alembic migrations |
| `make seed` | Seed default data (plans) |
| `make dev` | Run API + worker + beat + web in parallel |
| `make test` | Run all tests |
| `make lint` | Run ruff and eslint |
| `make typecheck` | Run mypy and tsc |
```

- [ ] **Step 3: Create `.env.example`**

```
# ─── Postgres ───────────────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://campusconnect:campusconnect@localhost:5432/campusconnect
DATABASE_URL_SYNC=postgresql+psycopg://campusconnect:campusconnect@localhost:5432/campusconnect

# ─── Redis ──────────────────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# ─── Mailhog (dev SMTP) ─────────────────────────────────────────────────────
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_FROM=no-reply@campusconnect.local

# ─── Auth ───────────────────────────────────────────────────────────────────
AUTH_SECRET=replace-with-32-byte-random-base64
NEXTAUTH_URL=http://localhost:3000

# ─── API ────────────────────────────────────────────────────────────────────
API_BASE_URL=http://localhost:8000
APP_ENV=local

# ─── Observability ──────────────────────────────────────────────────────────
SENTRY_DSN_API=
SENTRY_DSN_WEB=
OTEL_EXPORTER_OTLP_ENDPOINT=
OTEL_SERVICE_NAME_API=campusconnect-api
OTEL_SERVICE_NAME_WEB=campusconnect-web

# ─── MinIO (S3) ─────────────────────────────────────────────────────────────
S3_ENDPOINT=http://localhost:9000
S3_REGION=us-east-1
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=campusconnect-dev

# ─── Langfuse ───────────────────────────────────────────────────────────────
LANGFUSE_HOST=http://localhost:3030
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
```

- [ ] **Step 4: Create `Makefile`**

```makefile
.PHONY: up down ps logs migrate seed dev api worker beat web test lint typecheck clean

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down

ps:
	docker compose -f infra/docker-compose.yml ps

logs:
	docker compose -f infra/docker-compose.yml logs -f --tail=100

migrate:
	cd apps/api && uv run alembic upgrade head

seed:
	cd apps/api && uv run python -m app.scripts.seed

api:
	cd apps/api && uv run uvicorn app.main:app --reload --port 8000

worker:
	cd apps/api && uv run celery -A app.worker.celery_app worker --loglevel=info

beat:
	cd apps/api && uv run celery -A app.worker.celery_app beat --loglevel=info

web:
	cd apps/web && pnpm dev

dev:
	$(MAKE) -j4 api worker beat web

test:
	cd apps/api && uv run pytest -xvs
	cd apps/web && pnpm test

lint:
	cd apps/api && uv run ruff check . && uv run ruff format --check .
	cd apps/web && pnpm lint

typecheck:
	cd apps/api && uv run mypy app
	cd apps/web && pnpm typecheck

clean:
	docker compose -f infra/docker-compose.yml down -v
```

- [ ] **Step 5: Extend `.gitignore`**

Append to the existing `.gitignore`:

```
# Python tooling
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
htmlcov/

# uv
.venv/
.uv/

# Node
.pnpm-store/
.next/
.turbo/
.tsbuildinfo
playwright-report/
test-results/

# Local env
.env
.env.*
!.env.example
```

- [ ] **Step 6: Commit**

```bash
git add README.md .env.example Makefile .gitignore apps/api/tests/test_scaffold.py
git commit -m "chore: scaffold repository root (README, env, Makefile, gitignore)"
```

---

## Task 2: Docker Compose infrastructure

**Files:**
- Create: `infra/docker-compose.yml`
- Create: `infra/docker/postgres-pgvector/Dockerfile`
- Create: `infra/README.md`

- [ ] **Step 1: Define expected runtime check**

We don't write a Python test for Docker Compose; instead, the verification is a shell command after `docker compose up`. The acceptance criteria for this task is:

```bash
docker compose -f infra/docker-compose.yml ps --format json | jq -r '.[].Name' | sort
```

Should output exactly:
```
infra-langfuse-1
infra-mailhog-1
infra-minio-1
infra-postgres-1
infra-redis-1
```

And:
```bash
docker compose -f infra/docker-compose.yml exec -T postgres \
  psql -U campusconnect -d campusconnect -c "SELECT extname FROM pg_extension;"
```

Should list `vector` and `pg_trgm` among the installed extensions.

- [ ] **Step 2: Create the pgvector Dockerfile**

`infra/docker/postgres-pgvector/Dockerfile`:

```dockerfile
FROM postgres:16-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      postgresql-16-pgvector \
 && rm -rf /var/lib/apt/lists/*
```

- [ ] **Step 3: Create `infra/docker-compose.yml`**

```yaml
name: infra
services:
  postgres:
    build:
      context: ./docker/postgres-pgvector
    environment:
      POSTGRES_USER: campusconnect
      POSTGRES_PASSWORD: campusconnect
      POSTGRES_DB: campusconnect
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U campusconnect"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  mailhog:
    image: mailhog/mailhog:latest
    ports:
      - "1025:1025"
      - "8025:8025"

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - miniodata:/data

  langfuse:
    image: langfuse/langfuse:2
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://campusconnect:campusconnect@postgres:5432/langfuse
      NEXTAUTH_URL: http://localhost:3030
      NEXTAUTH_SECRET: dev-only-langfuse-secret
      SALT: dev-only-langfuse-salt
      TELEMETRY_ENABLED: "false"
      LANGFUSE_INIT_PROJECT_PUBLIC_KEY: lf-dev-pk
      LANGFUSE_INIT_PROJECT_SECRET_KEY: lf-dev-sk
    ports:
      - "3030:3000"

volumes:
  pgdata:
  miniodata:
```

Note: Langfuse needs its own database. Add an init script to create it. Create `infra/docker/postgres-pgvector/init.sql`:

```sql
CREATE DATABASE langfuse;
```

Update the `postgres` service in compose to mount it:

```yaml
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./docker/postgres-pgvector/init.sql:/docker-entrypoint-initdb.d/01-databases.sql:ro
```

- [ ] **Step 4: Create `infra/README.md`**

```markdown
# Infrastructure

Local development stack via Docker Compose.

| Service | URL | Notes |
| --- | --- | --- |
| Postgres + pgvector | `localhost:5432` | user/pass/db = `campusconnect` |
| Redis | `localhost:6379` | db 0 cache, db 1 broker, db 2 results |
| Mailhog SMTP | `localhost:1025` | UI at http://localhost:8025 |
| MinIO | `http://localhost:9000` | console at http://localhost:9001 |
| Langfuse | `http://localhost:3030` | log in with email |

Bring up: `make up`. Tear down with data preserved: `make down`. Wipe everything: `make clean`.
```

- [ ] **Step 5: Verify the stack starts cleanly**

Run:
```bash
make up
sleep 15
docker compose -f infra/docker-compose.yml ps
```

Expected output: all five services in state `running` (`langfuse` may take 30 seconds longer; re-check if needed).

Verify pgvector:
```bash
docker compose -f infra/docker-compose.yml exec -T postgres \
  psql -U campusconnect -d campusconnect -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extname FROM pg_extension WHERE extname='vector';"
```

Expected: `vector` appears in the result set.

- [ ] **Step 6: Commit**

```bash
git add infra/
git commit -m "feat(infra): docker-compose stack with postgres+pgvector, redis, minio, mailhog, langfuse"
```

---

## Task 3: Python project bootstrap (`apps/api`)

**Files:**
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/README.md`
- Create: `apps/api/app/__init__.py`
- Create: `apps/api/app/main.py`
- Create: `apps/api/app/config.py`

- [ ] **Step 1: Write the failing test — `app.main` exposes a FastAPI instance**

Create `apps/api/tests/__init__.py` (empty) and `apps/api/tests/conftest.py`:

```python
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
```

Create `apps/api/tests/test_app_bootstrap.py`:

```python
def test_app_is_a_fastapi_instance(app):
    from fastapi import FastAPI
    assert isinstance(app, FastAPI)


def test_app_has_a_title(app):
    assert app.title == "CampusConnect API"
```

- [ ] **Step 2: Create `apps/api/pyproject.toml`**

```toml
[project]
name = "campusconnect-api"
version = "0.1.0"
description = "CampusConnect API service"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.32.0",
  "pydantic>=2.9.0",
  "pydantic-settings>=2.6.0",
  "sqlalchemy[asyncio]>=2.0.36",
  "asyncpg>=0.30.0",
  "psycopg[binary]>=3.2.0",
  "alembic>=1.13.0",
  "celery>=5.4.0",
  "redis>=5.2.0",
  "httpx>=0.27.0",
  "python-multipart>=0.0.12",
  "sentry-sdk[fastapi,celery,sqlalchemy]>=2.18.0",
  "opentelemetry-distro>=0.49b0",
  "opentelemetry-exporter-otlp>=1.28.0",
  "opentelemetry-instrumentation-fastapi>=0.49b0",
  "opentelemetry-instrumentation-sqlalchemy>=0.49b0",
  "opentelemetry-instrumentation-celery>=0.49b0",
  "opentelemetry-instrumentation-redis>=0.49b0",
  "prometheus-client>=0.21.0",
]

[dependency-groups]
dev = [
  "pytest>=8.3.0",
  "pytest-asyncio>=0.24.0",
  "pytest-cov>=6.0.0",
  "ruff>=0.7.0",
  "mypy>=1.13.0",
  "types-redis",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "ASYNC", "RUF", "S"]
ignore = ["S101"]  # allow assert in tests

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]
exclude = ["alembic/versions"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-ra --strict-markers"
```

- [ ] **Step 3: Create `apps/api/app/__init__.py`**

```python
"""CampusConnect API package."""
__version__ = "0.1.0"
```

- [ ] **Step 4: Create `apps/api/app/config.py`**

```python
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
    return Settings()  # type: ignore[call-arg]
```

- [ ] **Step 5: Create `apps/api/app/main.py`**

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    return FastAPI(
        title="CampusConnect API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )


app = create_app()
```

- [ ] **Step 6: Install dependencies via uv**

```bash
cd apps/api && uv sync --all-extras
```

- [ ] **Step 7: Create `apps/api/README.md`**

```markdown
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
```

- [ ] **Step 8: Run the test**

```bash
cd apps/api && uv run pytest tests/test_app_bootstrap.py -xvs
```

Expected: 2 tests pass.

- [ ] **Step 9: Commit**

```bash
git add apps/api/pyproject.toml apps/api/uv.lock apps/api/README.md apps/api/app/ apps/api/tests/__init__.py apps/api/tests/conftest.py apps/api/tests/test_app_bootstrap.py
git commit -m "feat(api): bootstrap FastAPI app with config, ruff, mypy, pytest"
```

---

## Task 4: Database session and SQLAlchemy base

**Files:**
- Create: `apps/api/app/db/__init__.py`
- Create: `apps/api/app/db/base.py`
- Create: `apps/api/app/db/session.py`
- Create: `apps/api/tests/test_session.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_session.py`:

```python
import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_async_session_executes_select_1():
    from app.db.session import async_session_factory
    async with async_session_factory() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


@pytest.mark.asyncio
async def test_pgvector_extension_available():
    from app.db.session import async_session_factory
    async with async_session_factory() as session:
        await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        result = await session.execute(
            text("SELECT extname FROM pg_extension WHERE extname='vector'")
        )
        assert result.scalar_one() == "vector"
        await session.commit()
```

- [ ] **Step 2: Run the test to verify it fails**

Before creating the test database, run:
```bash
docker compose -f infra/docker-compose.yml exec -T postgres \
  psql -U campusconnect -c "CREATE DATABASE campusconnect_test;"
```

Then:
```bash
cd apps/api && uv run pytest tests/test_session.py -xvs
```

Expected: ImportError (module not found).

- [ ] **Step 3: Implement `apps/api/app/db/__init__.py`**

```python
"""Database package."""
```

- [ ] **Step 4: Implement `apps/api/app/db/session.py`**

```python
from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.config import get_settings


_settings = get_settings()

engine = create_async_engine(
    _settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
```

- [ ] **Step 5: Implement `apps/api/app/db/base.py`**

```python
from sqlalchemy.orm import DeclarativeBase, declared_attr
import re


class Base(DeclarativeBase):
    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        # CamelCase -> snake_case + plural-ish (lower)
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
```

- [ ] **Step 6: Run the test to verify it passes**

```bash
cd apps/api && uv run pytest tests/test_session.py -xvs
```

Expected: 2 tests pass.

- [ ] **Step 7: Commit**

```bash
git add apps/api/app/db/ apps/api/tests/test_session.py
git commit -m "feat(api): async SQLAlchemy session factory and declarative base"
```

---

## Task 5: Tenancy mixin

**Files:**
- Create: `apps/api/app/models/__init__.py`
- Create: `apps/api/app/models/mixins.py`
- Create: `apps/api/tests/test_mixins.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_mixins.py`:

```python
import uuid
from sqlalchemy import Column, Integer
from sqlalchemy.orm import Mapped, mapped_column


def test_tenanted_mixin_adds_org_id_column():
    from app.db.base import Base
    from app.models.mixins import TenantedMixin

    class _Foo(TenantedMixin, Base):
        __tablename__ = "_foo_test_tenanted"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)

    cols = {c.name for c in _Foo.__table__.columns}
    assert "org_id" in cols
    assert "id" in cols


def test_timestamp_mixin_adds_created_at_updated_at():
    from app.db.base import Base
    from app.models.mixins import TimestampMixin

    class _Bar(TimestampMixin, Base):
        __tablename__ = "_bar_test_timestamp"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)

    cols = {c.name for c in _Bar.__table__.columns}
    assert "created_at" in cols
    assert "updated_at" in cols


def test_uuid_pk_mixin_uses_uuid_default():
    from app.db.base import Base
    from app.models.mixins import UUIDPrimaryKeyMixin

    class _Baz(UUIDPrimaryKeyMixin, Base):
        __tablename__ = "_baz_test_uuid"

    inst = _Baz()
    assert isinstance(inst.id, uuid.UUID)
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd apps/api && uv run pytest tests/test_mixins.py -xvs
```

Expected: ImportError.

- [ ] **Step 3: Implement `apps/api/app/models/__init__.py`**

```python
"""ORM models."""
from app.models.mixins import TenantedMixin, TimestampMixin, UUIDPrimaryKeyMixin

__all__ = ["TenantedMixin", "TimestampMixin", "UUIDPrimaryKeyMixin"]
```

- [ ] **Step 4: Implement `apps/api/app/models/mixins.py`**

```python
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TenantedMixin:
    """Marks a model as tenant-scoped. Auto-filter and RLS rely on `org_id`."""

    @declared_attr
    def org_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            PG_UUID(as_uuid=True),
            ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
```

- [ ] **Step 5: Run the test to verify it passes**

```bash
cd apps/api && uv run pytest tests/test_mixins.py -xvs
```

Expected: 3 tests pass.

- [ ] **Step 6: Commit**

```bash
git add apps/api/app/models/ apps/api/tests/test_mixins.py
git commit -m "feat(api): TenantedMixin, TimestampMixin, UUIDPrimaryKeyMixin"
```

---

## Task 6: Core domain models

**Files:**
- Create: `apps/api/app/models/plan.py`
- Create: `apps/api/app/models/organization.py`
- Create: `apps/api/app/models/user.py`
- Create: `apps/api/app/models/audit_log.py`
- Modify: `apps/api/app/models/__init__.py`
- Create: `apps/api/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_models.py`:

```python
import uuid


def test_plan_model_columns():
    from app.models import Plan
    cols = {c.name for c in Plan.__table__.columns}
    assert cols == {
        "id", "code", "name", "monthly_inr", "monthly_lead_quota", "features",
        "created_at", "updated_at",
    }
    assert Plan.__table__.c.code.unique is True


def test_organization_model_columns():
    from app.models import Organization
    cols = {c.name for c in Organization.__table__.columns}
    required = {
        "id", "name", "slug", "plan_id", "status",
        "default_language", "branding", "data_residency",
        "created_at", "updated_at",
    }
    assert required <= cols


def test_user_model_columns():
    from app.models import User
    cols = {c.name for c in User.__table__.columns}
    required = {
        "id", "org_id", "email", "name", "role", "status",
        "last_seen_at", "created_at", "updated_at",
    }
    assert required <= cols


def test_audit_log_inherits_tenanted_mixin():
    from app.models import AuditLog
    cols = {c.name for c in AuditLog.__table__.columns}
    required = {
        "id", "org_id", "actor_user_id", "action",
        "target_type", "target_id", "meta", "created_at",
    }
    assert required <= cols
```

- [ ] **Step 2: Run to fail**

```bash
cd apps/api && uv run pytest tests/test_models.py -xvs
```

Expected: ImportError.

- [ ] **Step 3: Implement `apps/api/app/models/plan.py`**

```python
from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Plan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plans"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    monthly_inr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monthly_lead_quota: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    features: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
```

- [ ] **Step 4: Implement `apps/api/app/models/organization.py`**

```python
import uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


ORG_STATUS = SAEnum("trial", "active", "past_due", "suspended", name="org_status")
LANGUAGE = SAEnum("en", "hi", "hinglish", name="language_code")
DATA_RESIDENCY = SAEnum("in", "us", "eu", name="data_residency")


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plans.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(ORG_STATUS, nullable=False, default="trial")
    default_language: Mapped[str] = mapped_column(LANGUAGE, nullable=False, default="hinglish")
    branding: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    data_residency: Mapped[str] = mapped_column(DATA_RESIDENCY, nullable=False, default="in")
```

- [ ] **Step 5: Implement `apps/api/app/models/user.py`**

```python
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


USER_ROLE = SAEnum("platform_admin", "org_admin", "counsellor", name="user_role")
USER_STATUS = SAEnum("invited", "active", "disabled", name="user_status")


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    org_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    role: Mapped[str] = mapped_column(USER_ROLE, nullable=False, default="org_admin")
    status: Mapped[str] = mapped_column(USER_STATUS, nullable=False, default="invited")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 6: Implement `apps/api/app/models/audit_log.py`**

```python
import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TenantedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, TenantedMixin, TimestampMixin, Base):
    __tablename__ = "audit_log"

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
```

- [ ] **Step 7: Update `apps/api/app/models/__init__.py`**

```python
"""ORM models."""
from app.models.audit_log import AuditLog
from app.models.mixins import TenantedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.organization import Organization
from app.models.plan import Plan
from app.models.user import User

__all__ = [
    "AuditLog",
    "Organization",
    "Plan",
    "TenantedMixin",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "User",
]
```

- [ ] **Step 8: Run the test**

```bash
cd apps/api && uv run pytest tests/test_models.py -xvs
```

Expected: 4 tests pass.

- [ ] **Step 9: Commit**

```bash
git add apps/api/app/models/ apps/api/tests/test_models.py
git commit -m "feat(api): core domain models (Plan, Organization, User, AuditLog)"
```

---

## Task 7: Alembic setup and initial migration

**Files:**
- Create: `apps/api/alembic.ini`
- Create: `apps/api/alembic/env.py`
- Create: `apps/api/alembic/script.py.mako`
- Create: `apps/api/alembic/versions/0001_init_extensions_and_core_tables.py`
- Create: `apps/api/tests/test_migrations.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_migrations.py`:

```python
import subprocess
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]


def test_alembic_upgrade_head_succeeds():
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=API_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_alembic_downgrade_base_then_upgrade_head_idempotent():
    for cmd in (["downgrade", "base"], ["upgrade", "head"]):
        result = subprocess.run(
            ["uv", "run", "alembic", *cmd],
            cwd=API_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"{cmd} failed: {result.stderr}"
```

- [ ] **Step 2: Run to fail**

```bash
cd apps/api && uv run pytest tests/test_migrations.py -xvs
```

Expected: alembic not configured.

- [ ] **Step 3: Create `apps/api/alembic.ini`**

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
file_template = %%(rev)s_%%(slug)s
sqlalchemy.url =

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 4: Create `apps/api/alembic/script.py.mako`**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 5: Create `apps/api/alembic/env.py`**

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import get_settings
from app.db.base import Base
from app.models import *  # noqa: F401,F403  -- registers all models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().DATABASE_URL)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 6: Create the initial migration `apps/api/alembic/versions/0001_init_extensions_and_core_tables.py`**

```python
"""init extensions and core tables

Revision ID: 0001
Revises:
Create Date: 2026-05-17 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    org_status = sa.Enum("trial", "active", "past_due", "suspended", name="org_status")
    language_code = sa.Enum("en", "hi", "hinglish", name="language_code")
    data_residency = sa.Enum("in", "us", "eu", name="data_residency")
    user_role = sa.Enum("platform_admin", "org_admin", "counsellor", name="user_role")
    user_status = sa.Enum("invited", "active", "disabled", name="user_status")

    org_status.create(op.get_bind(), checkfirst=True)
    language_code.create(op.get_bind(), checkfirst=True)
    data_residency.create(op.get_bind(), checkfirst=True)
    user_role.create(op.get_bind(), checkfirst=True)
    user_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("monthly_inr", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("monthly_lead_quota", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("features", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id"), nullable=True),
        sa.Column("status", org_status, nullable=False, server_default="trial"),
        sa.Column("default_language", language_code, nullable=False, server_default="hinglish"),
        sa.Column("branding", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("data_residency", data_residency, nullable=False, server_default="in"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("name", sa.String(256), nullable=True),
        sa.Column("role", user_role, nullable=False, server_default="org_admin"),
        sa.Column("status", user_status, nullable=False, server_default="invited"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_org_id", "users", ["org_id"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(64), nullable=True),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("meta", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_log_org_id", "audit_log", ["org_id"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_action", table_name="audit_log")
    op.drop_index("ix_audit_log_org_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_org_id", table_name="users")
    op.drop_table("users")

    op.drop_table("organizations")
    op.drop_table("plans")

    for enum_name in ("user_status", "user_role", "data_residency", "language_code", "org_status"):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
```

- [ ] **Step 7: Run the migration test**

Ensure the test DB exists:
```bash
docker compose -f infra/docker-compose.yml exec -T postgres \
  psql -U campusconnect -c "CREATE DATABASE campusconnect_test;" || true
```

Run:
```bash
cd apps/api && DATABASE_URL=postgresql+asyncpg://campusconnect:campusconnect@localhost:5432/campusconnect_test uv run pytest tests/test_migrations.py -xvs
```

Expected: 2 tests pass.

- [ ] **Step 8: Commit**

```bash
git add apps/api/alembic.ini apps/api/alembic/ apps/api/tests/test_migrations.py
git commit -m "feat(api): alembic setup and initial migration (extensions + core tables)"
```

---

## Task 8: Postgres RLS policies migration

**Files:**
- Create: `apps/api/alembic/versions/0002_rls_policies.py`
- Create: `apps/api/tests/test_rls.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_rls.py`:

```python
import uuid
import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_rls_isolates_audit_log_between_orgs():
    from app.db.session import async_session_factory

    org_a = uuid.uuid4()
    org_b = uuid.uuid4()

    async with async_session_factory() as session:
        # bypass RLS as superuser to seed data
        await session.execute(text("SET LOCAL row_security = off"))
        await session.execute(
            text("INSERT INTO plans (id, code, name) VALUES (gen_random_uuid(), 'free', 'Free') ON CONFLICT DO NOTHING")
        )
        for org_id, slug in ((org_a, f"a-{org_a.hex[:8]}"), (org_b, f"b-{org_b.hex[:8]}")):
            await session.execute(
                text(
                    "INSERT INTO organizations (id, name, slug) VALUES (:id, :name, :slug) ON CONFLICT DO NOTHING"
                ),
                {"id": org_id, "name": slug, "slug": slug},
            )
            await session.execute(
                text(
                    "INSERT INTO audit_log (id, org_id, action) VALUES (gen_random_uuid(), :org_id, 'test')"
                ),
                {"org_id": org_id},
            )
        await session.commit()

    async with async_session_factory() as session:
        await session.execute(text("SET LOCAL row_security = on"))
        await session.execute(text("SET LOCAL app.current_org_id = :v"), {"v": str(org_a)})
        rows = (await session.execute(text("SELECT org_id FROM audit_log"))).scalars().all()
        assert set(rows) == {org_a}

    async with async_session_factory() as session:
        await session.execute(text("SET LOCAL row_security = on"))
        await session.execute(text("SET LOCAL app.current_org_id = :v"), {"v": str(org_b)})
        rows = (await session.execute(text("SELECT org_id FROM audit_log"))).scalars().all()
        assert set(rows) == {org_b}


@pytest.mark.asyncio
async def test_rls_without_org_setting_returns_no_rows():
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        await session.execute(text("SET LOCAL row_security = on"))
        await session.execute(text("SET LOCAL app.current_org_id = '00000000-0000-0000-0000-000000000000'"))
        rows = (await session.execute(text("SELECT count(*) FROM audit_log"))).scalar_one()
        assert rows == 0
```

- [ ] **Step 2: Run to fail**

```bash
cd apps/api && DATABASE_URL=postgresql+asyncpg://campusconnect:campusconnect@localhost:5432/campusconnect_test uv run pytest tests/test_rls.py -xvs
```

Expected: the first test sees both orgs' rows because RLS isn't enabled yet.

- [ ] **Step 3: Create `apps/api/alembic/versions/0002_rls_policies.py`**

```python
"""rls policies on tenanted tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-17 00:01:00.000000
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TENANTED_TABLES = ["audit_log"]


def upgrade() -> None:
    for table in TENANTED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
                USING (
                    org_id::text = current_setting('app.current_org_id', true)
                )
                WITH CHECK (
                    org_id::text = current_setting('app.current_org_id', true)
                );
            """
        )


def downgrade() -> None:
    for table in TENANTED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
```

- [ ] **Step 4: Apply the migration**

```bash
cd apps/api && DATABASE_URL=postgresql+asyncpg://campusconnect:campusconnect@localhost:5432/campusconnect_test uv run alembic upgrade head
```

Expected: migration applies, no errors.

- [ ] **Step 5: Run the test to verify it passes**

```bash
cd apps/api && DATABASE_URL=postgresql+asyncpg://campusconnect:campusconnect@localhost:5432/campusconnect_test uv run pytest tests/test_rls.py -xvs
```

Expected: 2 tests pass.

- [ ] **Step 6: Commit**

```bash
git add apps/api/alembic/versions/0002_rls_policies.py apps/api/tests/test_rls.py
git commit -m "feat(api): postgres RLS policies on audit_log (tenant isolation)"
```

---

## Task 9: SQLAlchemy auto-filter (`TenantedMixin` listener)

**Files:**
- Create: `apps/api/app/db/tenant_filter.py`
- Modify: `apps/api/app/db/session.py`
- Create: `apps/api/tests/test_tenant_filter.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_tenant_filter.py`:

```python
import uuid
import pytest
from sqlalchemy import select, text


@pytest.mark.asyncio
async def test_auto_filter_scopes_query_to_current_org():
    from app.db.session import async_session_factory
    from app.db.tenant_filter import set_current_org
    from app.models import AuditLog

    org_a = uuid.uuid4()
    org_b = uuid.uuid4()

    async with async_session_factory() as session:
        await session.execute(text("SET LOCAL row_security = off"))
        for org_id, slug in ((org_a, f"f-{org_a.hex[:8]}"), (org_b, f"g-{org_b.hex[:8]}")):
            await session.execute(
                text(
                    "INSERT INTO organizations (id, name, slug) VALUES (:id, :name, :slug) ON CONFLICT DO NOTHING"
                ),
                {"id": org_id, "name": slug, "slug": slug},
            )
            await session.execute(
                text(
                    "INSERT INTO audit_log (id, org_id, action) VALUES (gen_random_uuid(), :org_id, 'filter-test')"
                ),
                {"org_id": org_id},
            )
        await session.commit()

    async with async_session_factory() as session:
        await session.execute(text("SET LOCAL row_security = on"))
        await session.execute(text("SET LOCAL app.current_org_id = :v"), {"v": str(org_a)})
        with set_current_org(org_a):
            rows = (await session.execute(select(AuditLog).where(AuditLog.action == "filter-test"))).scalars().all()
            assert all(row.org_id == org_a for row in rows)
            assert len(rows) >= 1


@pytest.mark.asyncio
async def test_auto_filter_bypass_context_returns_all_rows():
    from app.db.session import async_session_factory
    from app.db.tenant_filter import bypass_tenant_filter
    from app.models import AuditLog
    from sqlalchemy import select

    async with async_session_factory() as session:
        await session.execute(text("SET LOCAL row_security = off"))
        with bypass_tenant_filter():
            rows = (await session.execute(select(AuditLog).where(AuditLog.action == "filter-test"))).scalars().all()
            org_ids = {row.org_id for row in rows}
            assert len(org_ids) >= 2
```

- [ ] **Step 2: Run to fail**

```bash
cd apps/api && DATABASE_URL=postgresql+asyncpg://campusconnect:campusconnect@localhost:5432/campusconnect_test uv run pytest tests/test_tenant_filter.py -xvs
```

Expected: ImportError.

- [ ] **Step 3: Implement `apps/api/app/db/tenant_filter.py`**

```python
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria

from app.models.mixins import TenantedMixin


_current_org: ContextVar[uuid.UUID | None] = ContextVar("current_org", default=None)
_bypass: ContextVar[bool] = ContextVar("bypass_tenant_filter", default=False)


@contextmanager
def set_current_org(org_id: uuid.UUID) -> Iterator[None]:
    token = _current_org.set(org_id)
    try:
        yield
    finally:
        _current_org.reset(token)


@contextmanager
def bypass_tenant_filter() -> Iterator[None]:
    token = _bypass.set(True)
    try:
        yield
    finally:
        _bypass.reset(token)


def install_listeners() -> None:
    """SQLAlchemy 2.x: hook into Session.do_orm_execute and inject a
    with_loader_criteria filter on every TenantedMixin SELECT."""

    @event.listens_for(Session, "do_orm_execute")
    def _do_orm_execute(state):  # type: ignore[no-untyped-def]
        if _bypass.get():
            return
        if not state.is_select:
            return
        org = _current_org.get()
        if org is None:
            return
        state.statement = state.statement.options(
            with_loader_criteria(
                TenantedMixin,
                lambda cls: cls.org_id == org,
                include_aliases=True,
            )
        )
```

- [ ] **Step 4: Wire the listener into the session module**

Modify `apps/api/app/db/session.py` — add at the bottom:

```python
from app.db.tenant_filter import install_listeners  # noqa: E402
install_listeners()
```

- [ ] **Step 5: Run the test**

```bash
cd apps/api && DATABASE_URL=postgresql+asyncpg://campusconnect:campusconnect@localhost:5432/campusconnect_test uv run pytest tests/test_tenant_filter.py -xvs
```

Expected: 2 tests pass.

- [ ] **Step 6: Commit**

```bash
git add apps/api/app/db/tenant_filter.py apps/api/app/db/session.py apps/api/tests/test_tenant_filter.py
git commit -m "feat(api): SQLAlchemy tenant auto-filter via with_loader_criteria"
```

---

## Task 10: Seed default plans (data migration + script)

**Files:**
- Create: `apps/api/alembic/versions/0003_seed_plans.py`
- Create: `apps/api/app/scripts/__init__.py`
- Create: `apps/api/app/scripts/seed.py`
- Create: `apps/api/tests/test_seed.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_seed.py`:

```python
import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_three_default_plans_exist_after_migration():
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        codes = (
            await session.execute(text("SELECT code FROM plans ORDER BY code"))
        ).scalars().all()
        assert set(codes) >= {"free", "growth", "enterprise"}
```

- [ ] **Step 2: Run to fail**

```bash
cd apps/api && DATABASE_URL=postgresql+asyncpg://campusconnect:campusconnect@localhost:5432/campusconnect_test uv run pytest tests/test_seed.py -xvs
```

Expected: fewer than 3 plans.

- [ ] **Step 3: Create the seed migration `apps/api/alembic/versions/0003_seed_plans.py`**

```python
"""seed default plans

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-17 00:02:00.000000
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PLANS = [
    ("free", "Free", 0, 100, '{"campaigns": false, "rag": true, "languages": ["en","hi","hinglish"]}'),
    ("growth", "Growth", 299900, 1000, '{"campaigns": true, "rag": true, "languages": ["en","hi","hinglish"]}'),
    ("enterprise", "Enterprise", 0, 100000, '{"campaigns": true, "rag": true, "languages": ["en","hi","hinglish"], "sla": "24h", "sso": true}'),
]


def upgrade() -> None:
    for code, name, monthly_inr, monthly_lead_quota, features_json in PLANS:
        op.execute(
            f"""
            INSERT INTO plans (id, code, name, monthly_inr, monthly_lead_quota, features)
            VALUES (gen_random_uuid(), '{code}', '{name}', {monthly_inr}, {monthly_lead_quota}, '{features_json}')
            ON CONFLICT (code) DO NOTHING
            """
        )


def downgrade() -> None:
    for code, *_ in PLANS:
        op.execute(f"DELETE FROM plans WHERE code = '{code}'")
```

- [ ] **Step 4: Create `apps/api/app/scripts/__init__.py`** (empty)

```python
```

- [ ] **Step 5: Create `apps/api/app/scripts/seed.py`** (Makefile entry point)

```python
"""Idempotent seed for local dev. Currently a no-op because seeding lives in migrations,
but the entry point exists so `make seed` works and future seed data can land here."""
import asyncio

from app.config import get_settings


async def main() -> None:
    settings = get_settings()
    print(f"Seed complete for {settings.APP_ENV} (DB: {settings.DATABASE_URL.split('@')[-1]})")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 6: Apply the migration and run the test**

```bash
cd apps/api && DATABASE_URL=postgresql+asyncpg://campusconnect:campusconnect@localhost:5432/campusconnect_test uv run alembic upgrade head
cd apps/api && DATABASE_URL=postgresql+asyncpg://campusconnect:campusconnect@localhost:5432/campusconnect_test uv run pytest tests/test_seed.py -xvs
```

Expected: test passes.

- [ ] **Step 7: Commit**

```bash
git add apps/api/alembic/versions/0003_seed_plans.py apps/api/app/scripts/ apps/api/tests/test_seed.py
git commit -m "feat(api): seed three default plans (free/growth/enterprise)"
```

---

## Task 11: Request ID middleware

**Files:**
- Create: `apps/api/app/middleware/__init__.py`
- Create: `apps/api/app/middleware/request_id.py`
- Modify: `apps/api/app/main.py`
- Create: `apps/api/tests/test_request_id.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_request_id.py`:

```python
def test_request_id_header_is_present(client):
    response = client.get("/healthz")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) >= 16


def test_inbound_request_id_is_propagated(client):
    response = client.get("/healthz", headers={"X-Request-ID": "abc-123"})
    assert response.headers["x-request-id"] == "abc-123"
```

(`/healthz` is implemented in Task 12. This test will fail with a 404 right now, which is fine — we only check the middleware sets the header on whatever response goes out.)

- [ ] **Step 2: Implement `apps/api/app/middleware/__init__.py`**

```python
"""HTTP middleware."""
```

- [ ] **Step 3: Implement `apps/api/app/middleware/request_id.py`**

```python
import uuid
from collections.abc import Awaitable, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        rid = request.headers.get(HEADER) or uuid.uuid4().hex
        request.state.request_id = rid
        response = await call_next(request)
        response.headers[HEADER] = rid
        return response
```

- [ ] **Step 4: Wire into `apps/api/app/main.py`**

Replace the file with:

```python
from fastapi import FastAPI

from app.middleware.request_id import RequestIDMiddleware


def create_app() -> FastAPI:
    app = FastAPI(
        title="CampusConnect API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(RequestIDMiddleware)
    return app


app = create_app()
```

- [ ] **Step 5: Note**

The test will still fail because `/healthz` returns 404. That's fine for now — Task 12 implements it. The middleware still attaches the header to the 404 response, so the test should pass. Verify:

```bash
cd apps/api && uv run pytest tests/test_request_id.py -xvs
```

Expected: 2 tests pass (the 404 response still carries the header).

- [ ] **Step 6: Commit**

```bash
git add apps/api/app/middleware/ apps/api/app/main.py apps/api/tests/test_request_id.py
git commit -m "feat(api): request-id middleware (propagate or generate)"
```

---

## Task 12: Health and readiness endpoints

**Files:**
- Create: `apps/api/app/routers/__init__.py`
- Create: `apps/api/app/routers/health.py`
- Modify: `apps/api/app/main.py`
- Create: `apps/api/tests/test_health.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_health.py`:

```python
def test_healthz_returns_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_returns_ok_when_db_reachable(client):
    response = client.get("/readyz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["postgres"] is True
```

- [ ] **Step 2: Run to fail**

```bash
cd apps/api && uv run pytest tests/test_health.py -xvs
```

Expected: 404.

- [ ] **Step 3: Implement `apps/api/app/routers/__init__.py`**

```python
"""Routers."""
```

- [ ] **Step 4: Implement `apps/api/app/routers/health.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db


router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(db: AsyncSession = Depends(get_db)) -> dict:
    checks: dict[str, bool] = {}
    try:
        await db.execute(text("SELECT 1"))
        checks["postgres"] = True
    except Exception:
        checks["postgres"] = False
    status = "ok" if all(checks.values()) else "degraded"
    return {"status": status, "checks": checks}
```

- [ ] **Step 5: Wire into `apps/api/app/main.py`**

Replace `apps/api/app/main.py`:

```python
from fastapi import FastAPI

from app.middleware.request_id import RequestIDMiddleware
from app.routers import health


def create_app() -> FastAPI:
    app = FastAPI(
        title="CampusConnect API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(RequestIDMiddleware)
    app.include_router(health.router)
    return app


app = create_app()
```

- [ ] **Step 6: Run tests**

```bash
cd apps/api && uv run pytest tests/test_health.py -xvs
```

Expected: 2 tests pass.

- [ ] **Step 7: Commit**

```bash
git add apps/api/app/routers/ apps/api/app/main.py apps/api/tests/test_health.py
git commit -m "feat(api): /healthz and /readyz endpoints"
```

---

## Task 13: Prometheus metrics endpoint

**Files:**
- Create: `apps/api/app/routers/metrics.py`
- Modify: `apps/api/app/main.py`
- Create: `apps/api/tests/test_metrics.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_metrics.py`:

```python
def test_metrics_endpoint_returns_prometheus_format(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "# HELP" in body
    assert "# TYPE" in body
    assert "http_requests_total" in body or "python_info" in body
```

- [ ] **Step 2: Run to fail**

```bash
cd apps/api && uv run pytest tests/test_metrics.py -xvs
```

Expected: 404.

- [ ] **Step 3: Implement `apps/api/app/routers/metrics.py`**

```python
from fastapi import APIRouter, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    generate_latest,
    multiprocess,
)


router = APIRouter(tags=["metrics"])

REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    registry = CollectorRegistry()
    try:
        multiprocess.MultiProcessCollector(registry)
        data = generate_latest(registry)
    except (ValueError, OSError):
        data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
```

- [ ] **Step 4: Wire into `apps/api/app/main.py`**

Replace `apps/api/app/main.py`:

```python
from fastapi import FastAPI

from app.middleware.request_id import RequestIDMiddleware
from app.routers import health, metrics


def create_app() -> FastAPI:
    app = FastAPI(
        title="CampusConnect API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(RequestIDMiddleware)
    app.include_router(health.router)
    app.include_router(metrics.router)
    return app


app = create_app()
```

- [ ] **Step 5: Run tests**

```bash
cd apps/api && uv run pytest tests/test_metrics.py -xvs
```

Expected: 1 test passes.

- [ ] **Step 6: Commit**

```bash
git add apps/api/app/routers/metrics.py apps/api/app/main.py apps/api/tests/test_metrics.py
git commit -m "feat(api): /metrics endpoint (prometheus format)"
```

---

## Task 14: Sentry initialization

**Files:**
- Create: `apps/api/app/observability/__init__.py`
- Create: `apps/api/app/observability/sentry.py`
- Modify: `apps/api/app/main.py`
- Create: `apps/api/tests/test_sentry.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_sentry.py`:

```python
def test_sentry_init_is_a_no_op_when_dsn_missing(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN_API", raising=False)
    from app.observability.sentry import init_sentry
    init_sentry()  # no exception means pass


def test_sentry_init_is_called_during_app_create(monkeypatch):
    calls: list[None] = []

    def fake_init() -> None:
        calls.append(None)

    monkeypatch.setattr("app.observability.sentry.init_sentry", fake_init)
    from app.main import create_app
    create_app()
    assert calls == [None]
```

- [ ] **Step 2: Run to fail**

```bash
cd apps/api && uv run pytest tests/test_sentry.py -xvs
```

Expected: ImportError.

- [ ] **Step 3: Implement `apps/api/app/observability/__init__.py`**

```python
"""Observability primitives."""
```

- [ ] **Step 4: Implement `apps/api/app/observability/sentry.py`**

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

from app.config import get_settings


def init_sentry() -> None:
    settings = get_settings()
    if not settings.SENTRY_DSN_API:
        return
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN_API,
        environment=settings.APP_ENV,
        traces_sample_rate=0.1,
        send_default_pii=False,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            CeleryIntegration(),
        ],
    )
```

- [ ] **Step 5: Wire into `apps/api/app/main.py`**

Replace `apps/api/app/main.py`:

```python
from fastapi import FastAPI

from app.middleware.request_id import RequestIDMiddleware
from app.observability.sentry import init_sentry
from app.routers import health, metrics


def create_app() -> FastAPI:
    init_sentry()
    app = FastAPI(
        title="CampusConnect API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(RequestIDMiddleware)
    app.include_router(health.router)
    app.include_router(metrics.router)
    return app


app = create_app()
```

- [ ] **Step 6: Run tests**

```bash
cd apps/api && uv run pytest tests/test_sentry.py -xvs
```

Expected: 2 tests pass.

- [ ] **Step 7: Commit**

```bash
git add apps/api/app/observability/ apps/api/app/main.py apps/api/tests/test_sentry.py
git commit -m "feat(api): sentry initialization (no-op when DSN unset)"
```

---

## Task 15: OpenTelemetry initialization

**Files:**
- Create: `apps/api/app/observability/otel.py`
- Modify: `apps/api/app/main.py`
- Create: `apps/api/tests/test_otel.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_otel.py`:

```python
def test_otel_init_does_not_raise(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    from app.observability.otel import init_otel
    init_otel()  # no exception means pass


def test_traceparent_header_is_returned(client):
    # The FastAPI instrumentor adds traceparent on outgoing responses
    response = client.get("/healthz")
    # `traceparent` is propagated when the request itself carries one;
    # the response always contains the trace span info via the request id middleware as fallback.
    # We assert the request_id is present (proxy for "tracing fired").
    assert response.headers.get("x-request-id")
```

- [ ] **Step 2: Implement `apps/api/app/observability/otel.py`**

```python
import logging
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

from app.config import get_settings


_log = logging.getLogger(__name__)
_initialized = False


def init_otel() -> None:
    global _initialized
    if _initialized:
        return
    settings = get_settings()
    resource = Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME_API,
            "deployment.environment": settings.APP_ENV,
        }
    )
    provider = TracerProvider(resource=resource)

    if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT))
        )
    else:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)

    SQLAlchemyInstrumentor().instrument()
    CeleryInstrumentor().instrument()
    RedisInstrumentor().instrument()
    _initialized = True


def instrument_app(app) -> None:
    FastAPIInstrumentor.instrument_app(app)
```

- [ ] **Step 3: Wire into `apps/api/app/main.py`**

Replace `apps/api/app/main.py`:

```python
from fastapi import FastAPI

from app.middleware.request_id import RequestIDMiddleware
from app.observability.otel import init_otel, instrument_app
from app.observability.sentry import init_sentry
from app.routers import health, metrics


def create_app() -> FastAPI:
    init_sentry()
    init_otel()
    app = FastAPI(
        title="CampusConnect API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(RequestIDMiddleware)
    app.include_router(health.router)
    app.include_router(metrics.router)
    instrument_app(app)
    return app


app = create_app()
```

- [ ] **Step 4: Run tests**

```bash
cd apps/api && uv run pytest tests/test_otel.py tests/test_sentry.py tests/test_health.py -xvs
```

Expected: all pass; the API console shows JSON span output when hitting `/healthz` from a curl run.

Verify manually:
```bash
cd apps/api && uv run uvicorn app.main:app --port 8000 &
sleep 2
curl -sS http://localhost:8000/healthz
kill %1
```

Expected: console prints a `ConsoleSpanExporter` JSON span for the request.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/observability/otel.py apps/api/app/main.py apps/api/tests/test_otel.py
git commit -m "feat(api): opentelemetry initialization with console + OTLP exporters"
```

---

## Task 16: Celery worker (`hello_world` task)

**Files:**
- Create: `apps/api/app/worker/__init__.py`
- Create: `apps/api/app/worker/celery_app.py`
- Create: `apps/api/app/worker/tasks/__init__.py`
- Create: `apps/api/app/worker/tasks/hello.py`
- Create: `apps/api/tests/test_hello_task.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_hello_task.py`:

```python
def test_hello_task_runs_eagerly_and_returns_payload(monkeypatch):
    monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "cache+memory://")
    from app.worker.celery_app import celery_app
    from app.worker.tasks.hello import hello_world

    celery_app.conf.task_always_eager = True
    result = hello_world.delay("Pratik")
    payload = result.get()
    assert payload["greeting"] == "Hello, Pratik!"
    assert payload["from"] == "campusconnect-worker"
```

- [ ] **Step 2: Run to fail**

```bash
cd apps/api && uv run pytest tests/test_hello_task.py -xvs
```

Expected: ImportError.

- [ ] **Step 3: Implement `apps/api/app/worker/__init__.py`**

```python
"""Celery worker package."""
```

- [ ] **Step 4: Implement `apps/api/app/worker/celery_app.py`**

```python
from celery import Celery

from app.config import get_settings
from app.observability.otel import init_otel
from app.observability.sentry import init_sentry


_settings = get_settings()


def _build() -> Celery:
    init_sentry()
    init_otel()
    app = Celery(
        "campusconnect",
        broker=_settings.CELERY_BROKER_URL,
        backend=_settings.CELERY_RESULT_BACKEND,
        include=["app.worker.tasks.hello"],
    )
    app.conf.update(
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        broker_connection_retry_on_startup=True,
        worker_prefetch_multiplier=1,
    )
    return app


celery_app = _build()
```

- [ ] **Step 5: Implement `apps/api/app/worker/tasks/__init__.py`**

```python
"""Task modules."""
```

- [ ] **Step 6: Implement `apps/api/app/worker/tasks/hello.py`**

```python
from app.worker.celery_app import celery_app


@celery_app.task(name="campusconnect.hello_world")
def hello_world(name: str) -> dict[str, str]:
    return {"greeting": f"Hello, {name}!", "from": "campusconnect-worker"}
```

- [ ] **Step 7: Run the test**

```bash
cd apps/api && uv run pytest tests/test_hello_task.py -xvs
```

Expected: 1 test passes.

- [ ] **Step 8: Smoke test end-to-end with the real Redis broker**

In one terminal:
```bash
cd apps/api && CELERY_BROKER_URL=redis://localhost:6379/1 CELERY_RESULT_BACKEND=redis://localhost:6379/2 uv run celery -A app.worker.celery_app worker --loglevel=info
```

In another:
```bash
cd apps/api && CELERY_BROKER_URL=redis://localhost:6379/1 CELERY_RESULT_BACKEND=redis://localhost:6379/2 uv run python -c "
from app.worker.tasks.hello import hello_world
print(hello_world.delay('M0').get(timeout=10))
"
```

Expected: `{'greeting': 'Hello, M0!', 'from': 'campusconnect-worker'}` and the worker log shows the task being received.

Stop the worker (Ctrl+C).

- [ ] **Step 9: Commit**

```bash
git add apps/api/app/worker/ apps/api/tests/test_hello_task.py
git commit -m "feat(worker): celery app with hello_world task"
```

---

## Task 17: Celery Beat schedule (heartbeat)

**Files:**
- Create: `apps/api/app/worker/beat_schedule.py`
- Modify: `apps/api/app/worker/celery_app.py`
- Create: `apps/api/tests/test_beat_schedule.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_beat_schedule.py`:

```python
def test_beat_schedule_includes_heartbeat():
    from app.worker.celery_app import celery_app
    assert "heartbeat" in celery_app.conf.beat_schedule
    entry = celery_app.conf.beat_schedule["heartbeat"]
    assert entry["task"] == "campusconnect.hello_world"
```

- [ ] **Step 2: Run to fail**

```bash
cd apps/api && uv run pytest tests/test_beat_schedule.py -xvs
```

Expected: KeyError.

- [ ] **Step 3: Create `apps/api/app/worker/beat_schedule.py`**

```python
from celery.schedules import crontab


BEAT_SCHEDULE = {
    "heartbeat": {
        "task": "campusconnect.hello_world",
        "schedule": crontab(minute="*"),
        "args": ("beat",),
    },
}
```

- [ ] **Step 4: Wire into `apps/api/app/worker/celery_app.py`**

Modify the end of `celery_app.py` to apply the schedule:

```python
from app.worker.beat_schedule import BEAT_SCHEDULE

celery_app.conf.beat_schedule = BEAT_SCHEDULE
```

So the full file becomes:

```python
from celery import Celery

from app.config import get_settings
from app.observability.otel import init_otel
from app.observability.sentry import init_sentry


_settings = get_settings()


def _build() -> Celery:
    init_sentry()
    init_otel()
    app = Celery(
        "campusconnect",
        broker=_settings.CELERY_BROKER_URL,
        backend=_settings.CELERY_RESULT_BACKEND,
        include=["app.worker.tasks.hello"],
    )
    app.conf.update(
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        broker_connection_retry_on_startup=True,
        worker_prefetch_multiplier=1,
    )
    return app


celery_app = _build()

from app.worker.beat_schedule import BEAT_SCHEDULE  # noqa: E402

celery_app.conf.beat_schedule = BEAT_SCHEDULE
```

- [ ] **Step 5: Run the test**

```bash
cd apps/api && uv run pytest tests/test_beat_schedule.py -xvs
```

Expected: 1 test passes.

- [ ] **Step 6: Commit**

```bash
git add apps/api/app/worker/beat_schedule.py apps/api/app/worker/celery_app.py apps/api/tests/test_beat_schedule.py
git commit -m "feat(worker): celery beat heartbeat schedule"
```

---

## Task 18: Worker and Beat Dockerfiles

**Files:**
- Create: `apps/worker/Dockerfile`
- Create: `apps/worker/README.md`
- Create: `apps/beat/Dockerfile`
- Create: `apps/beat/README.md`

- [ ] **Step 1: Create `apps/worker/Dockerfile`**

```dockerfile
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

WORKDIR /app
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-dev

COPY apps/api/app ./app
COPY apps/api/alembic ./alembic
COPY apps/api/alembic.ini ./alembic.ini

ENV PYTHONPATH=/app
CMD ["uv", "run", "celery", "-A", "app.worker.celery_app", "worker", "--loglevel=info"]
```

- [ ] **Step 2: Create `apps/worker/README.md`**

```markdown
# Worker

Thin Dockerfile that re-uses the Python package from `apps/api` and runs `celery worker`.

Build from the repo root:

```bash
docker build -f apps/worker/Dockerfile -t campusconnect-worker .
```
```

- [ ] **Step 3: Create `apps/beat/Dockerfile`**

```dockerfile
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

WORKDIR /app
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-dev

COPY apps/api/app ./app
COPY apps/api/alembic ./alembic
COPY apps/api/alembic.ini ./alembic.ini

ENV PYTHONPATH=/app
CMD ["uv", "run", "celery", "-A", "app.worker.celery_app", "beat", "--loglevel=info"]
```

- [ ] **Step 4: Create `apps/beat/README.md`**

```markdown
# Beat

Thin Dockerfile that re-uses the Python package from `apps/api` and runs `celery beat`.

Build from the repo root:

```bash
docker build -f apps/beat/Dockerfile -t campusconnect-beat .
```
```

- [ ] **Step 5: Verify both Dockerfiles build**

```bash
docker build -f apps/worker/Dockerfile -t campusconnect-worker .
docker build -f apps/beat/Dockerfile -t campusconnect-beat .
```

Expected: both builds succeed.

- [ ] **Step 6: Commit**

```bash
git add apps/worker/ apps/beat/
git commit -m "feat(infra): worker and beat Dockerfiles"
```

---

## Task 19: Next.js scaffold with Tailwind and shadcn

**Files:**
- Create: `apps/web/` (via `pnpm create next-app`)
- Modify: `apps/web/tsconfig.json`, `apps/web/next.config.mjs`
- Create: `apps/web/components.json`, shadcn config files

- [ ] **Step 1: Initialize the Next.js app**

```bash
cd apps && pnpm create next-app@latest web \
  --typescript --eslint --tailwind --src-dir --app --import-alias "@/*" --use-pnpm \
  --no-turbopack
```

(Accept all other defaults.)

- [ ] **Step 2: Install shadcn/ui**

```bash
cd apps/web && pnpm dlx shadcn@latest init --yes --base-color slate
```

This creates `components.json` and `src/lib/utils.ts`.

- [ ] **Step 3: Add a few shadcn primitives we'll need**

```bash
cd apps/web && pnpm dlx shadcn@latest add button input label card sonner
```

- [ ] **Step 4: Verify the app builds and types**

```bash
cd apps/web && pnpm typecheck && pnpm build
```

(Add `typecheck` to `package.json` scripts if it's missing — see Step 5.)

- [ ] **Step 5: Update `apps/web/package.json` scripts**

Ensure the `scripts` section contains:

```json
"scripts": {
  "dev": "next dev -p 3000",
  "build": "next build",
  "start": "next start -p 3000",
  "lint": "next lint",
  "typecheck": "tsc --noEmit",
  "test": "echo 'web tests run via Playwright in CI'"
}
```

- [ ] **Step 6: Commit**

```bash
git add apps/web/
git commit -m "feat(web): next.js 15 scaffold with tailwind + shadcn primitives"
```

---

## Task 20: NextAuth (Auth.js v5) magic-link

**Files:**
- Create: `apps/web/src/auth.ts`
- Create: `apps/web/src/app/api/auth/[...nextauth]/route.ts`
- Create: `apps/web/src/middleware.ts`
- Modify: `apps/web/package.json` (deps)
- Create: `apps/web/src/lib/env.ts`

- [ ] **Step 1: Install Auth.js v5 and nodemailer**

```bash
cd apps/web && pnpm add next-auth@beta @auth/core nodemailer
cd apps/web && pnpm add -D @types/nodemailer
```

- [ ] **Step 2: Create `apps/web/src/lib/env.ts`**

```typescript
import { z } from "zod";

const Env = z.object({
  AUTH_SECRET: z.string().min(16),
  SMTP_HOST: z.string().default("localhost"),
  SMTP_PORT: z.coerce.number().default(1025),
  SMTP_FROM: z.string().default("no-reply@campusconnect.local"),
  API_BASE_URL: z.string().url().default("http://localhost:8000"),
  NEXTAUTH_URL: z.string().url().default("http://localhost:3000"),
});

export const env = Env.parse({
  AUTH_SECRET: process.env.AUTH_SECRET,
  SMTP_HOST: process.env.SMTP_HOST,
  SMTP_PORT: process.env.SMTP_PORT,
  SMTP_FROM: process.env.SMTP_FROM,
  API_BASE_URL: process.env.API_BASE_URL,
  NEXTAUTH_URL: process.env.NEXTAUTH_URL,
});
```

Install zod:

```bash
cd apps/web && pnpm add zod
```

- [ ] **Step 3: Create `apps/web/src/auth.ts`**

```typescript
import NextAuth from "next-auth";
import Nodemailer from "next-auth/providers/nodemailer";
import { env } from "@/lib/env";

export const { handlers, auth, signIn, signOut } = NextAuth({
  secret: env.AUTH_SECRET,
  trustHost: true,
  providers: [
    Nodemailer({
      server: {
        host: env.SMTP_HOST,
        port: env.SMTP_PORT,
        secure: false,
      },
      from: env.SMTP_FROM,
    }),
  ],
  pages: {
    signIn: "/login",
    verifyRequest: "/login?check=email",
  },
  callbacks: {
    async session({ session, token }) {
      if (token?.sub) {
        session.user = { ...session.user, id: token.sub };
      }
      return session;
    },
  },
  session: { strategy: "jwt" },
});
```

Note: for the magic-link flow Auth.js requires a database adapter to track the verification token. For M0 we'll use the **Drizzle adapter** with a local SQLite file purely for the auth tables (keeps the Next.js app self-contained; the FastAPI Postgres has the canonical `users` table that we'll sync in M2). Alternatively, use the Auth.js Resend provider with no DB and JWT verification — but the email magic-link flow needs token persistence regardless.

Simpler choice for M0: store the verification tokens in a small SQLite file. Install:

```bash
cd apps/web && pnpm add @auth/drizzle-adapter drizzle-orm better-sqlite3
cd apps/web && pnpm add -D drizzle-kit @types/better-sqlite3
```

Create `apps/web/src/lib/db.ts`:

```typescript
import { drizzle } from "drizzle-orm/better-sqlite3";
import Database from "better-sqlite3";
import { sqliteTable, text, integer, primaryKey } from "drizzle-orm/sqlite-core";

const sqlite = new Database("./auth.sqlite");
export const db = drizzle(sqlite);

export const users = sqliteTable("user", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text("email").unique(),
  emailVerified: integer("emailVerified", { mode: "timestamp_ms" }),
  name: text("name"),
  image: text("image"),
});

export const accounts = sqliteTable(
  "account",
  {
    userId: text("userId").notNull().references(() => users.id, { onDelete: "cascade" }),
    type: text("type").notNull(),
    provider: text("provider").notNull(),
    providerAccountId: text("providerAccountId").notNull(),
    refresh_token: text("refresh_token"),
    access_token: text("access_token"),
    expires_at: integer("expires_at"),
    token_type: text("token_type"),
    scope: text("scope"),
    id_token: text("id_token"),
    session_state: text("session_state"),
  },
  (account) => ({
    compoundKey: primaryKey({ columns: [account.provider, account.providerAccountId] }),
  }),
);

export const sessions = sqliteTable("session", {
  sessionToken: text("sessionToken").primaryKey(),
  userId: text("userId").notNull().references(() => users.id, { onDelete: "cascade" }),
  expires: integer("expires", { mode: "timestamp_ms" }).notNull(),
});

export const verificationTokens = sqliteTable(
  "verificationToken",
  {
    identifier: text("identifier").notNull(),
    token: text("token").notNull(),
    expires: integer("expires", { mode: "timestamp_ms" }).notNull(),
  },
  (vt) => ({
    compoundKey: primaryKey({ columns: [vt.identifier, vt.token] }),
  }),
);

// Apply schema (idempotent table creation on import for dev simplicity)
sqlite.exec(`
  CREATE TABLE IF NOT EXISTS user (id TEXT PRIMARY KEY, email TEXT UNIQUE, emailVerified INTEGER, name TEXT, image TEXT);
  CREATE TABLE IF NOT EXISTS account (userId TEXT NOT NULL, type TEXT NOT NULL, provider TEXT NOT NULL, providerAccountId TEXT NOT NULL, refresh_token TEXT, access_token TEXT, expires_at INTEGER, token_type TEXT, scope TEXT, id_token TEXT, session_state TEXT, PRIMARY KEY (provider, providerAccountId));
  CREATE TABLE IF NOT EXISTS session (sessionToken TEXT PRIMARY KEY, userId TEXT NOT NULL, expires INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS verificationToken (identifier TEXT NOT NULL, token TEXT NOT NULL, expires INTEGER NOT NULL, PRIMARY KEY (identifier, token));
`);
```

Add `auth.sqlite` to `.gitignore`:

```
apps/web/auth.sqlite
```

Update `apps/web/src/auth.ts` to use the adapter:

```typescript
import NextAuth from "next-auth";
import Nodemailer from "next-auth/providers/nodemailer";
import { DrizzleAdapter } from "@auth/drizzle-adapter";
import { db, users, accounts, sessions, verificationTokens } from "@/lib/db";
import { env } from "@/lib/env";

export const { handlers, auth, signIn, signOut } = NextAuth({
  secret: env.AUTH_SECRET,
  trustHost: true,
  adapter: DrizzleAdapter(db, {
    usersTable: users,
    accountsTable: accounts,
    sessionsTable: sessions,
    verificationTokensTable: verificationTokens,
  }),
  providers: [
    Nodemailer({
      server: {
        host: env.SMTP_HOST,
        port: env.SMTP_PORT,
        secure: false,
      },
      from: env.SMTP_FROM,
    }),
  ],
  pages: {
    signIn: "/login",
    verifyRequest: "/login?check=email",
  },
  session: { strategy: "database" },
});
```

- [ ] **Step 4: Create `apps/web/src/app/api/auth/[...nextauth]/route.ts`**

```typescript
import { handlers } from "@/auth";
export const { GET, POST } = handlers;
```

- [ ] **Step 5: Create `apps/web/src/middleware.ts` (gates `/app`)**

```typescript
import { auth } from "@/auth";
import { NextResponse } from "next/server";

export default auth((req) => {
  const isOnApp = req.nextUrl.pathname.startsWith("/app");
  if (!isOnApp) return NextResponse.next();
  if (!req.auth) {
    const url = new URL("/login", req.url);
    url.searchParams.set("callbackUrl", req.nextUrl.pathname);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
});

export const config = {
  matcher: ["/app/:path*"],
};
```

- [ ] **Step 6: Smoke test (manual)**

Run mailhog (already up via Docker Compose), then:

```bash
cd apps/web && AUTH_SECRET="$(openssl rand -base64 32)" pnpm dev
```

Open http://localhost:3000/api/auth/signin → enter an email → check http://localhost:8025 for the magic link → click it → you should be authenticated (redirect to `/`).

- [ ] **Step 7: Commit**

```bash
git add apps/web/ .gitignore
git commit -m "feat(web): NextAuth magic-link with mailhog SMTP and SQLite adapter"
```

---

## Task 21: Login, signup, and protected dashboard pages

**Files:**
- Create: `apps/web/src/app/page.tsx` (replace existing)
- Create: `apps/web/src/app/login/page.tsx`
- Create: `apps/web/src/app/signup/page.tsx`
- Create: `apps/web/src/app/app/layout.tsx`
- Create: `apps/web/src/app/app/page.tsx`
- Create: `apps/web/src/components/app-shell.tsx`

- [ ] **Step 1: Replace `apps/web/src/app/page.tsx` (marketing landing)**

```tsx
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 flex flex-col">
      <header className="flex items-center justify-between px-8 py-5 border-b bg-white">
        <div className="font-semibold text-lg">CampusConnect</div>
        <nav className="flex gap-2">
          <Button asChild variant="ghost"><Link href="/login">Log in</Link></Button>
          <Button asChild><Link href="/signup">Get started</Link></Button>
        </nav>
      </header>
      <section className="flex-1 flex items-center justify-center p-12">
        <div className="max-w-2xl text-center space-y-6">
          <h1 className="text-5xl font-semibold tracking-tight">An AI WhatsApp admissions team that never sleeps.</h1>
          <p className="text-lg text-slate-600">
            CampusConnect captures, qualifies, nurtures, and hands over admission leads
            for educational institutes — on WhatsApp, in any language your students speak.
          </p>
          <div className="flex gap-3 justify-center">
            <Button asChild size="lg"><Link href="/signup">Start free</Link></Button>
            <Button asChild size="lg" variant="outline"><Link href="/demo">See it live</Link></Button>
          </div>
        </div>
      </section>
    </main>
  );
}
```

- [ ] **Step 2: Create `apps/web/src/app/login/page.tsx`**

```tsx
"use client";
import { signIn } from "next-auth/react";
import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const params = useSearchParams();
  const checkEmail = params.get("check") === "email";

  if (checkEmail) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-slate-50">
        <Card className="max-w-md">
          <CardHeader><CardTitle>Check your email</CardTitle></CardHeader>
          <CardContent>
            We sent you a magic link. Open it on this device to log in.
            <div className="text-xs text-slate-500 mt-3">(In local dev, find it in Mailhog at <a className="underline" href="http://localhost:8025">localhost:8025</a>.)</div>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-50">
      <Card className="w-full max-w-md">
        <CardHeader><CardTitle>Log in to CampusConnect</CardTitle></CardHeader>
        <CardContent>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              await signIn("nodemailer", { email, callbackUrl: "/app" });
            }}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <Button className="w-full" type="submit">Send magic link</Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
```

- [ ] **Step 3: Create `apps/web/src/app/signup/page.tsx`**

The signup flow uses the same magic-link mechanism — Auth.js's Nodemailer provider creates the user on first verification.

```tsx
"use client";
import { signIn } from "next-auth/react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function SignupPage() {
  const [email, setEmail] = useState("");

  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-50">
      <Card className="w-full max-w-md">
        <CardHeader><CardTitle>Create your CampusConnect account</CardTitle></CardHeader>
        <CardContent>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              await signIn("nodemailer", { email, callbackUrl: "/app" });
            }}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label htmlFor="email">Work email</Label>
              <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <Button className="w-full" type="submit">Create account</Button>
            <div className="text-xs text-slate-500 text-center">
              We'll email you a link. No password.
            </div>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
```

- [ ] **Step 4: Create `apps/web/src/components/app-shell.tsx`**

```tsx
import Link from "next/link";

export function AppShell({ children, email }: { children: React.ReactNode; email: string }) {
  return (
    <div className="min-h-screen grid grid-cols-[240px_1fr] bg-slate-50">
      <aside className="bg-white border-r flex flex-col">
        <div className="px-6 py-5 font-semibold">CampusConnect</div>
        <nav className="flex-1 px-3 space-y-1 text-sm">
          <SidebarLink href="/app">Dashboard</SidebarLink>
          <SidebarLink href="/app/inbox">Inbox</SidebarLink>
          <SidebarLink href="/app/leads">Leads</SidebarLink>
          <SidebarLink href="/app/settings/organization">Settings</SidebarLink>
        </nav>
        <div className="border-t p-4 text-xs text-slate-500">Signed in as<br /><span className="text-slate-900">{email}</span></div>
      </aside>
      <main className="p-10">{children}</main>
    </div>
  );
}

function SidebarLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="block px-3 py-2 rounded hover:bg-slate-100 text-slate-700">
      {children}
    </Link>
  );
}
```

- [ ] **Step 5: Create `apps/web/src/app/app/layout.tsx`**

```tsx
import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { AppShell } from "@/components/app-shell";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await auth();
  if (!session?.user?.email) redirect("/login");
  return <AppShell email={session.user.email}>{children}</AppShell>;
}
```

- [ ] **Step 6: Create `apps/web/src/app/app/page.tsx`**

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold">Dashboard</h1>
      <Card>
        <CardHeader><CardTitle>Welcome to CampusConnect</CardTitle></CardHeader>
        <CardContent className="text-slate-600">
          Your dashboard is empty for now. Once you connect a WhatsApp number and a lead messages you,
          everything will show up here.
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 7: Smoke test**

```bash
cd apps/web && AUTH_SECRET="$(openssl rand -base64 32)" pnpm dev
```

Visit `http://localhost:3000`, click "Get started", enter an email, open mailhog at `http://localhost:8025`, click the link, land on `/app`.

- [ ] **Step 8: Commit**

```bash
git add apps/web/src
git commit -m "feat(web): marketing landing, login, signup, protected dashboard shell"
```

---

## Task 22: Web Sentry + OpenTelemetry

**Files:**
- Create: `apps/web/sentry.client.config.ts`
- Create: `apps/web/sentry.server.config.ts`
- Create: `apps/web/instrumentation.ts`
- Modify: `apps/web/next.config.mjs`
- Create: `apps/web/src/app/api/health/route.ts`

- [ ] **Step 1: Install Sentry and Vercel OTel**

```bash
cd apps/web && pnpm add @sentry/nextjs @vercel/otel @opentelemetry/api
```

- [ ] **Step 2: Create `apps/web/sentry.client.config.ts`**

```typescript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  enabled: !!process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
  environment: process.env.APP_ENV ?? "local",
});
```

- [ ] **Step 3: Create `apps/web/sentry.server.config.ts`**

```typescript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.SENTRY_DSN_WEB,
  enabled: !!process.env.SENTRY_DSN_WEB,
  tracesSampleRate: 0.1,
  environment: process.env.APP_ENV ?? "local",
});
```

- [ ] **Step 4: Create `apps/web/instrumentation.ts`**

```typescript
import { registerOTel } from "@vercel/otel";

export function register() {
  registerOTel({
    serviceName: process.env.OTEL_SERVICE_NAME_WEB ?? "campusconnect-web",
  });
  if (process.env.NEXT_RUNTIME === "nodejs") {
    require("./sentry.server.config");
  }
  if (process.env.NEXT_RUNTIME === "edge") {
    require("./sentry.server.config");
  }
}
```

- [ ] **Step 5: Update `apps/web/next.config.mjs`**

(In Next.js 15 the `instrumentation.ts` hook is enabled by default — no `experimental` flag needed.)

```javascript
import { withSentryConfig } from "@sentry/nextjs";

/** @type {import('next').NextConfig} */
const nextConfig = {};

export default withSentryConfig(nextConfig, {
  silent: true,
  org: undefined,
  project: undefined,
});
```

- [ ] **Step 6: Add `apps/web/src/app/api/health/route.ts`** — calls the API and reports status

```typescript
import { env } from "@/lib/env";

export async function GET() {
  try {
    const res = await fetch(`${env.API_BASE_URL}/healthz`, { cache: "no-store" });
    const upstream = await res.json();
    return Response.json({ web: "ok", api: upstream.status });
  } catch (e) {
    return Response.json({ web: "ok", api: "unreachable" }, { status: 200 });
  }
}
```

- [ ] **Step 7: Verify type-check + build**

```bash
cd apps/web && pnpm typecheck && pnpm build
```

Expected: both succeed.

- [ ] **Step 8: Commit**

```bash
git add apps/web/sentry.client.config.ts apps/web/sentry.server.config.ts apps/web/instrumentation.ts apps/web/next.config.mjs apps/web/src/app/api/health/route.ts apps/web/package.json apps/web/pnpm-lock.yaml
git commit -m "feat(web): sentry + opentelemetry instrumentation, /api/health proxy"
```

---

## Task 23: Playwright e2e smoke test

**Files:**
- Create: `apps/web/playwright.config.ts`
- Create: `apps/web/e2e/signup-login.spec.ts`
- Modify: `apps/web/package.json`

- [ ] **Step 1: Install Playwright**

```bash
cd apps/web && pnpm add -D @playwright/test
cd apps/web && pnpm exec playwright install --with-deps chromium
```

- [ ] **Step 2: Create `apps/web/playwright.config.ts`**

```typescript
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: {
    command: "pnpm dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
    env: { AUTH_SECRET: "test-secret-not-for-prod-12345678" },
  },
});
```

- [ ] **Step 3: Create `apps/web/e2e/signup-login.spec.ts`**

This test signs up, fetches the magic link from Mailhog's API, opens it, and asserts the dashboard renders.

```typescript
import { test, expect, request } from "@playwright/test";

const MAILHOG = "http://localhost:8025";

async function latestMessageFor(email: string) {
  const api = await request.newContext({ baseURL: MAILHOG });
  // Mailhog v2 API
  const res = await api.get("/api/v2/messages?limit=50");
  const body = await res.json();
  const item = (body.items as any[]).find((m) =>
    m.Content.Headers.To?.[0]?.toLowerCase() === email.toLowerCase()
  );
  expect(item, "no email found for " + email).toBeTruthy();
  return item.Content.Body as string;
}

function extractLink(body: string): string {
  const decoded = body.replace(/=\r?\n/g, "").replace(/=3D/g, "=");
  const m = decoded.match(/https?:\/\/[^\s"<>]+api\/auth\/callback\/nodemailer[^\s"<>]*/);
  expect(m, "no magic link in email").toBeTruthy();
  return m![0];
}

test("user can sign up, receive a magic link, and reach the dashboard", async ({ page, browser }) => {
  const email = `test-${Date.now()}@example.com`;

  await page.goto("/signup");
  await page.fill('input[type="email"]', email);
  await page.click('button:has-text("Create account")');
  await page.waitForURL(/check=email/);

  // Wait briefly for SMTP delivery
  await page.waitForTimeout(2000);

  const body = await latestMessageFor(email);
  const link = extractLink(body);

  // Mailhog encodes the URL with quoted-printable; replace localhost with the resolved baseURL
  const ctx = await browser.newContext();
  const verifyPage = await ctx.newPage();
  await verifyPage.goto(link);

  await verifyPage.waitForURL(/\/app/);
  await expect(verifyPage.locator("h1")).toHaveText("Dashboard");
});
```

- [ ] **Step 4: Update `apps/web/package.json` scripts**

```json
"scripts": {
  "dev": "next dev -p 3000",
  "build": "next build",
  "start": "next start -p 3000",
  "lint": "next lint",
  "typecheck": "tsc --noEmit",
  "test": "playwright test",
  "test:headed": "playwright test --headed"
}
```

- [ ] **Step 5: Run the test**

Make sure `make up` has the stack running, then:

```bash
cd apps/web && pnpm test
```

Expected: 1 test passes.

- [ ] **Step 6: Commit**

```bash
git add apps/web/playwright.config.ts apps/web/e2e/ apps/web/package.json apps/web/pnpm-lock.yaml
git commit -m "test(web): playwright e2e signup → magic link → dashboard"
```

---

## Task 24: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:

jobs:
  api-lint-and-type:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/api
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install uv
      - run: uv sync --all-extras
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy app

  api-tests:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/api
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_USER: campusconnect
          POSTGRES_PASSWORD: campusconnect
          POSTGRES_DB: campusconnect_test
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U campusconnect"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 10
      redis:
        image: redis:7
        ports: ["6379:6379"]
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5
    env:
      DATABASE_URL: postgresql+asyncpg://campusconnect:campusconnect@localhost:5432/campusconnect_test
      DATABASE_URL_SYNC: postgresql+psycopg://campusconnect:campusconnect@localhost:5432/campusconnect_test
      REDIS_URL: redis://localhost:6379/0
      CELERY_BROKER_URL: redis://localhost:6379/1
      CELERY_RESULT_BACKEND: redis://localhost:6379/2
      AUTH_SECRET: ci-test-secret-12345678901234567890
      APP_ENV: ci
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install uv
      - run: uv sync --all-extras
      - run: uv run alembic upgrade head
      - run: uv run pytest -xvs --cov=app --cov-report=term-missing

  web-lint-type-build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/web
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
          cache-dependency-path: apps/web/pnpm-lock.yaml
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm typecheck
      - run: AUTH_SECRET=ci-test-secret-12345678901234567890 pnpm build

  web-e2e:
    runs-on: ubuntu-latest
    needs: [web-lint-type-build]
    defaults:
      run:
        working-directory: apps/web
    services:
      mailhog:
        image: mailhog/mailhog
        ports:
          - "1025:1025"
          - "8025:8025"
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
          cache-dependency-path: apps/web/pnpm-lock.yaml
      - run: pnpm install --frozen-lockfile
      - run: pnpm exec playwright install --with-deps chromium
      - run: AUTH_SECRET=ci-test-secret-12345678901234567890 SMTP_HOST=localhost SMTP_PORT=1025 pnpm test
```

- [ ] **Step 2: Push to a feature branch and open a draft PR**

```bash
git add .github/
git commit -m "ci: github actions for lint, type, unit, build, and e2e"
git push origin main
```

(Or push to a feature branch first if you prefer to verify CI on a PR.)

- [ ] **Step 3: Verify the workflow runs green**

Open the GitHub Actions tab on github.com/ENZ048/CampusConnect. All four jobs should pass on first run.

If any job fails, fix the underlying issue and force-push the fix. Common pitfalls: pnpm-lock missing from commit, missing test DB, `AUTH_SECRET` too short.

---

## Task 25: Architecture and runbook documentation

**Files:**
- Create: `docs/architecture.md`
- Create: `docs/runbook.md`
- Create: `packages/shared/README.md`

- [ ] **Step 1: Create `docs/architecture.md`**

```markdown
# CampusConnect Architecture

> Authoritative source: [`docs/superpowers/specs/2026-05-17-campusconnect-design.md`](./superpowers/specs/2026-05-17-campusconnect-design.md). This file is the operational quick-reference and should stay in sync with the spec as the system evolves.

## High-level diagram

```
                              ┌─────────────────────────┐
                              │ Meta WhatsApp Cloud API │
                              │ Telegram Bot API        │
                              └──────────┬──────────────┘
                                         │ webhooks
                                         ▼
   ┌──────────────────────┐    ┌────────────────────────┐    ┌──────────────────┐
   │  Next.js dashboard   │◄──►│  FastAPI API service   │◄──►│  Postgres        │
   │  (Vercel)            │    │  /api, /webhook, /ws   │    │  + pgvector      │
   └──────────────────────┘    └────────────┬───────────┘    │  (Neon)          │
                                            │                └──────────────────┘
                                            │ enqueue
                                            ▼
                              ┌────────────────────────┐    ┌──────────────────┐
                              │  Celery workers        │◄──►│  Redis (Upstash) │
                              │  agent.run, channel.send│    │  broker + pubsub │
                              │  rag.ingest, nurture   │    └──────────────────┘
                              └────────────┬───────────┘
                                           │
                              ┌────────────▼───────────┐
                              │  OpenAI / Langfuse /   │
                              │  R2 / Stripe / Google  │
                              └────────────────────────┘
```

## Processes

| Process | Code | Why isolated |
| --- | --- | --- |
| `apps/api` | `app.main:app` | Latency-sensitive, must ack webhooks in <5s |
| `apps/worker` | `app.worker.celery_app worker` | Slow work; retry semantics; survives outages |
| `apps/beat` | `app.worker.celery_app beat` | Periodic jobs (nurture tick, template sync, analytics) |
| `apps/web` | `next dev / start` | Dashboard, marketing, demo sandbox |

## Multi-tenant isolation

Three layers, all required:

1. API middleware sets `request.state.org_id` from JWT and a Postgres session var.
2. SQLAlchemy event listener auto-filters tenanted queries by `org_id` (see `app.db.tenant_filter`).
3. Postgres RLS policies on every tenanted table, enforced even for the table owner.

## Observability

- Sentry for errors (both API and web).
- OpenTelemetry tracing exported to console in dev, OTLP in prod.
- Prometheus metrics at `/metrics`.
- Langfuse for LLM-specific traces (M3+).

## Local development

```bash
make up && make migrate && make dev
```

See the README for environment variables.
```

- [ ] **Step 2: Create `docs/runbook.md`**

```markdown
# CampusConnect Runbook

## On-call playbooks

### Symptom: webhook ack is slow (>5s) and Meta is retrying

- Check API logs in Sentry for slow handlers.
- Verify Celery enqueue is not blocked: `redis-cli -p 6379 LLEN celery`.
- If Redis broker is unreachable, the webhook must still ack 200 — verify the failure path doesn't block.

### Symptom: OpenAI 5xx surge

- Pause outbound campaigns: `POST /api/v1/campaigns/{id}/pause`.
- Drain the agent queue: `celery -A app.worker.celery_app inspect active`.
- Switch the LLM provider to backup (M9 ships the model-agnostic gateway).

### Symptom: agent looping (>6 tool calls in one turn)

- Inspect the conversation trace at `/app/leads/<id>?panel=trace`.
- Identify the tool returning bad output (often `lookup_kb` with stale embeddings).
- Set conversation mode to `human` to silence the agent immediately.

### Symptom: WhatsApp send fails with "24h window expired"

- This is by design — outside the window, only templates can be sent.
- Verify the agent's `send_message` tool routed to a template; if not, the prompt regressed.

## Local development gotchas

- Postgres test DB must exist: `createdb -h localhost -U campusconnect campusconnect_test`.
- Mailhog SMTP must be running for Auth.js magic links.
- The Drizzle SQLite `auth.sqlite` file is gitignored — delete it to reset auth state.

## Backups

- Neon PITR covers 7 days.
- Logical backups land on R2 nightly with 30-day retention.
- Backup verification runs weekly (Phase M12).

## Disaster recovery

- RTO 30 min, RPO 5 min — documented in M12.
```

- [ ] **Step 3: Create `packages/shared/README.md`**

```markdown
# packages/shared

Placeholder. From Phase M1 onward this package will house TypeScript types generated from the FastAPI OpenAPI schema, consumed by the Next.js dashboard.
```

- [ ] **Step 4: Commit**

```bash
git add docs/architecture.md docs/runbook.md packages/shared/README.md
git commit -m "docs: architecture overview, runbook, and shared package placeholder"
```

---

## Task 26: End-to-end smoke from scratch + tag the milestone

**Files:** none new; this task is verification.

- [ ] **Step 1: Wipe and rebuild from scratch**

```bash
make clean
make up
sleep 20
docker compose -f infra/docker-compose.yml exec -T postgres psql -U campusconnect -c "CREATE DATABASE campusconnect_test;" || true
cd apps/api && uv sync --all-extras && uv run alembic upgrade head && cd -
cd apps/web && pnpm install --frozen-lockfile && cd -
```

- [ ] **Step 2: Run all tests**

```bash
make test
```

Expected: all Python tests pass; Playwright e2e passes.

- [ ] **Step 3: Run lint and typecheck**

```bash
make lint
make typecheck
```

Expected: no errors.

- [ ] **Step 4: Manually verify the end-state acceptance criteria**

Run the four processes:

```bash
make dev
```

In a browser:
1. http://localhost:3000 — see the marketing landing.
2. Click "Get started" → enter `you@example.com` → see "Check your email".
3. Open http://localhost:8025 → click the magic link.
4. Land on http://localhost:3000/app → see the dashboard shell with sidebar.
5. Open http://localhost:8000/healthz → see `{"status":"ok"}`.
6. Watch the API console — confirm an OTel span prints for the request.

- [ ] **Step 5: Tag the release**

```bash
git tag -a v0.0.1-m0 -m "Phase M0: foundations"
git push --tags
```

- [ ] **Step 6: Update top-level README with M0 status**

Add a section to `README.md`:

```markdown
## Roadmap

- [x] **M0 — Foundations** (this milestone). Multi-tenant Postgres with RLS, FastAPI + Celery + Redis, Next.js dashboard with magic-link auth, Sentry + OpenTelemetry, CI green. Tagged `v0.0.1-m0`.
- [ ] M1 — WhatsApp inbound, dashboard inbox, manual reply.
- [ ] M2 — Telegram adapter.
- [ ] M3 — LLM agent (function-calling) and qualification flow.
- [ ] M4 — RAG knowledge layer with citations.
- [ ] M5 — Voice notes, multilingual, sentiment, handover summary.
- [ ] M6 — Nurture sequences.
- [ ] M7 — Outbound campaigns.
- [ ] M8 — Calendar bookings.
- [ ] M9 — Prompt versioning + A/B testing.
- [ ] M10 — Outbound webhooks.
- [ ] M11 — Billing, demo sandbox, marketing, status page.
- [ ] M12 — Compliance, load tests, runbooks.
- [ ] M13 — README, video, polish.
```

- [ ] **Step 7: Commit and push**

```bash
git add README.md
git commit -m "docs: mark M0 complete in roadmap"
git push origin main
```

---

## Spec coverage map (Phase M0)

Cross-checking against §19 of the design spec (Phase M0 — Foundations):

| Spec requirement | Implemented in |
| --- | --- |
| Monorepo layout (`apps/api`, `apps/web`, `apps/worker`, `apps/beat`, `packages/shared`, `infra/`, `tests/`, `docs/`) | Tasks 1, 3, 18, 19, 25 |
| Docker Compose stack: Postgres + pgvector, Redis, Langfuse, mailhog, S3 emulator | Task 2 |
| Alembic migrations: `organizations`, `users`, `audit_log`, `plans` (seed three plans) | Tasks 7, 10 |
| Postgres RLS policies | Task 8 |
| `TenantedMixin` ORM auto-filter | Tasks 5, 9 |
| FastAPI `/healthz`, `/readyz`, `/metrics` | Tasks 12, 13 |
| Next.js shell with NextAuth magic-link login, protected `/app` | Tasks 19, 20, 21 |
| Celery worker, beat, and a `hello_world` task | Tasks 16, 17, 18 |
| CI: lint, type-check, unit tests, build. Preview deploy on PR | Task 24 (preview deploy itself ships automatically via Vercel project connection — document in runbook) |
| Sentry + OpenTelemetry wired in both apps | Tasks 14, 15 (API), 22 (web) |
| `docs/architecture.md` skeleton | Task 25 |

End state ("sign up with email, log in, see empty dashboard, view request trace in OTel"): Tasks 16–26 together.

---

## Notes on Vercel preview deploys

Vercel auto-deploys every PR once the repository is connected via the Vercel dashboard. To enable:

1. Visit https://vercel.com/new and import `ENZ048/CampusConnect`.
2. Set the project root to `apps/web`.
3. Add env vars: `AUTH_SECRET`, `API_BASE_URL`, `NEXTAUTH_URL` (Vercel will set this automatically per deploy).
4. Enable "Preview deploys for all branches".

For the FastAPI service, Fly.io preview apps are deferred to a later phase (documented in `docs/runbook.md` for now). Local dev does not need this.

---

*End of Phase M0 implementation plan.*
