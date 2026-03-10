# Quick Start

Instructions to bootstrap the development environment locally.

## Prerequisites

- **Docker** (20.10+) and **Docker Compose**
- **Python 3.11** (for running management scripts; not required for containers)
- **Node.js 20** (for frontend)

## Environment Setup

1. Copy the sample environment file:
   ```bash
   cp .env.dev .env
   ```
2. Fill in any required secrets (e.g. dummy JWT keys, database passwords).
3. Build and start the stack:
   ```bash
   make up
   ```
4. Run migrations:
   ```bash
   make migrate
   ```
5. (Optional) start ML inference worker if you plan to run async jobs:
   ```bash
   make ml-worker
   ```
   and/or start the scheduler to retrain models automatically:
   ```bash
   make beat
   ```
5. (Optional) load sample data:
6. Start the ML service (if you're working on model code):
   ```bash
   docker compose up -d ml_service
   ```
   ```bash
   docker-compose exec property_service python scripts/load_sample_data.py
   ```
6. Retrieve a JWT from the auth service to use with secured endpoints:

> **Tip:** you can adjust the in-memory ARV cache duration used by
> `property_service` via the `ARV_CACHE_TTL` environment variable (seconds,
> default 300). Restart the container after changing it.
>
> **Note:** the ML service retraining schedule is governed by
> `RETRAIN_CRON` in the env file (cron format, default `0 0 * * *`).  Change it
> for testing or to a monthly/weekly cadence.

   ```bash
   curl -s -X POST http://localhost:8001/auth/login \
        -H 'Content-Type: application/json' \
        -d '{"email":"user@example.com","password":"pass"}' | jq
   ```
   The returned `access_token` can be added as `Authorization: Bearer ...`.
7. Open the frontend at http://localhost:3000 (login page available at `/login`) and API at http://localhost:8002.

## Common Tasks

- Tail logs: `make logs`
- Run backend tests: `make test` (or `make property-test` / `make auth-test` for individual services)

- To exercise the ML job queue from the CLI you can:
  ```bash
  TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
           -H 'Content-Type: application/json' \
           -d '{"email":"user@example.com","password":"pass"}' | jq -r .access_token)
  # submit job
  JOBID=$(curl -s -X POST http://localhost:8003/ml/jobs \
            -H "Authorization: Bearer $TOKEN" \
            -H 'Content-Type: application/json' \
            -d '{"property_id":"00000000-0000-0000-0000-000000000000"}' | jq -r .task_id)
  echo "submitted job $JOBID"
  # poll status
  curl -s http://localhost:8003/ml/jobs/$JOBID -H "Authorization: Bearer $TOKEN" | jq
  ```

- To see which model artifacts are currently loaded:
  ```bash
  curl -s http://localhost:8003/ml/models -H "Authorization: Bearer $TOKEN" | jq
  # or via the property service proxy:
  curl -s http://localhost:8002/ml/models -H "Authorization: Bearer $TOKEN" | jq
  ```

- To enqueue a report via the report service directly:
  ```bash
  curl -s -X POST http://localhost:8004/reports \
        -H "Authorization: Bearer $TOKEN" \
        -H 'Content-Type: application/json' \
        -d '{"property_id":"00000000-0000-0000-0000-000000000000"}' | jq
  ```
  to check status:
  ```bash
  curl http://localhost:8004/reports/<task_id> -H "Authorization: Bearer $TOKEN" | jq
  ```
  or via the property service proxies:
  ```bash
  curl -s -X POST http://localhost:8002/properties/00000000-0000-0000-0000-000000000000/report \
        -H "Authorization: Bearer $TOKEN" | jq
  curl http://localhost:8002/properties/00000000-0000-0000-0000-000000000000/report_status/<task_id> -H "Authorization: Bearer $TOKEN" | jq
  ```
- Rebuild an individual service:
  ```bash
  docker compose build auth_service
  ```

## Cleanup

```bash
make down
docker volume prune
```

Refer to `docs/operating.md` for production runbook and backup commands.
