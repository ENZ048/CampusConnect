# Worker

Thin Dockerfile that re-uses the Python package from `apps/api` and runs `celery worker`.

Build from the repo root:

```bash
docker build -f apps/worker/Dockerfile -t campusconnect-worker .
```
