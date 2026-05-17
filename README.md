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

## Roadmap

- [x] **M0 - Foundations** (this milestone). Multi-tenant Postgres with RLS, FastAPI + Celery + Redis, Next.js dashboard with magic-link auth, Sentry + OpenTelemetry, CI green. Tagged `v0.0.1-m0`.
- [ ] M1 - WhatsApp inbound, dashboard inbox, manual reply.
- [ ] M2 - Telegram adapter.
- [ ] M3 - LLM agent (function-calling) and qualification flow.
- [ ] M4 - RAG knowledge layer with citations.
- [ ] M5 - Voice notes, multilingual, sentiment, handover summary.
- [ ] M6 - Nurture sequences.
- [ ] M7 - Outbound campaigns.
- [ ] M8 - Calendar bookings.
- [ ] M9 - Prompt versioning + A/B testing.
- [ ] M10 - Outbound webhooks.
- [ ] M11 - Billing, demo sandbox, marketing, status page.
- [ ] M12 - Compliance, load tests, runbooks.
- [ ] M13 - README, video, polish.
