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
