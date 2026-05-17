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
