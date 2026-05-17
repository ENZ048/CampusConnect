# Beat

Thin Dockerfile that re-uses the Python package from `apps/api` and runs `celery beat`.

Build from the repo root:

```bash
docker build -f apps/beat/Dockerfile -t campusconnect-beat .
```
