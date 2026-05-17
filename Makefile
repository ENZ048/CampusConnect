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
