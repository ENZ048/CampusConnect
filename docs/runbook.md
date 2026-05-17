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

- Postgres test DB must exist: create with `docker compose -f infra/docker-compose.yml exec -T postgres psql -U campusconnect -c "CREATE DATABASE campusconnect_test;"`.
- Mailhog SMTP must be running for Auth.js magic links.
- The Drizzle SQLite `auth.sqlite` file is gitignored — delete it to reset auth state.

## Backups

- Neon PITR covers 7 days.
- Logical backups land on R2 nightly with 30-day retention.
- Backup verification runs weekly (Phase M12).

## Disaster recovery

- RTO 30 min, RPO 5 min — documented in M12.
