# Microservice API Design

This document presents each FastAPI-based service, its responsibilities, ports,
internal dependencies, and key API endpoints.

## 5.1 Auth Service (port 8001)

- Built with FastAPI, `python-jose`, and `passlib[bcrypt]`.
- JWT access tokens (RS256) with 60‑minute TTL, refresh tokens (30 days) stored
  in Redis.
- Private key is mounted as a Docker secret; public key exposed for service-to-
  service verification.
- RBAC roles: `viewer`, `analyst`, `admin` enforced with FastAPI dependencies.
- Endpoints:
  - `POST /auth/login` – accepts email/password, returns access/refresh tokens.
  - `POST /auth/refresh` – exchanges refresh for new access token.
  - `POST /auth/logout` – revokes refresh token.
  - `GET /auth/health` – returns service/redis/db status.

Rate limiting is applied on login attempts (10/minute per IP) using `slowapi`.

## 5.2 Property Service (port 8002)

Core API for property functions; uses SQLAlchemy async ORM and `httpx` for
calling other services. Cursor-based pagination is implemented on list
endpoints.

### Important endpoints

- `GET /properties/search` – full-text & geospatial search (Meilisearch). Returns a structured JSON object with `hits`, `query`, `processingTimeMs`, etc. Suitable for direct frontend consumption.
- `GET /properties/{id}` – retrieve detailed property record
- `GET /properties/{id}/arv` – proxy to ML service; returns an ARV range for the property (requires auth).  The call includes a 10‑second timeout and will surface a 504 if the ML service is slow.  Results are cached in Redis (TTL ~5 min) to limit duplicate requests.
- `POST /properties/arv_batch` – forward a batch inference request to the ML service.
- `POST /properties/{id}/arv_async` – enqueue an asynchronous ARV job via the ML service and return a Celery task ID; useful for batch workflows.
- `GET /properties/{id}/arv_status/{task_id}` – check the status (and eventual result) of a previously submitted async job.
- `POST /properties/{id}/report` – request a PDF report for the property; returns a Celery task ID.
- `GET /properties/{id}/report_status/{task_id}` – query the status/result of a report job.
- `GET /ml/models` – list available ML model artifacts (proxied to `ml_service`).
- `GET /properties/{id}/comps` – comp selection API. The current
  implementation uses the property's address to query Meilisearch for similar
  records and returns a short list; future versions will add geospatial and
  date filters such as `radius`, `days`, `sqft_tolerance`, etc.

> **Authentication:** all write operations require a valid JWT access token
> in the `Authorization: Bearer <token>` header.  Tokens are issued by
> `auth_service` via `/auth/login` and are HS256‑signed using
> `JWT_SECRET_KEY`.

- `POST /properties` – create or update property (admin-only)
- `POST /properties/import` – development endpoint that queues a CSV ingestion job; accepts optional `filepath` parameter and returns Celery task ID.

Internal cache is stored in Redis with TTLs; updates flush relevant keys via
Redis Pub/Sub.

## 5.3 ML Service (port 8003)

Hosts the trained ARV models and orchestrates AI narrative generation using
LangChain. This service is lightweight in development and exposes both
synchronous and asynchronous endpoints.

- Loads model artifacts from the `model_store` volume at startup (not yet
  implemented).
- **Authentication:** every endpoint requires a valid JWT access token from the
  auth service.
- Synchronous inference endpoints:
  - `POST /ml/arv` – compute ARV range for a single property
  - `POST /ml/arv_batch` – compute ARV ranges for a list of property IDs
  - `POST /ml/narrative` – generate narrative text for provided context
  - `POST /ml/retrain` – trigger a model retraining job via Celery; also runs automatically via scheduler
- Asynchronous job submission:
  - `POST /ml/jobs` – enqueue scoring job via Celery; returns task ID
  - `GET /ml/jobs/{id}` – check status/result of an existing job using Celery task ID
- Additional Prometheus metrics:
  - `ml_models_loaded` gauge reporting number of artifacts in the model store
  - latency/version metrics (future work)

## 5.4 Report Service (port 8004)

Lightweight service for producing property reports.  For now the task
writes simple text files to demonstrate the workflow; in production these
would be real PDFs generated with tools such as WeasyPrint or ReportLab.
The service exposes both a synchronous status endpoint and a job
submission endpoint, and records a Prometheus counter when a report
is generated.

- `POST /reports` – enqueue report generation for a property ID (returns task
  ID)
- `GET /reports/{id}` – query job status; completed responses include a
  `download_path` pointing at the `report_output` volume.
- Output artifacts reside in `/app/report_output` (mapped to the
  `report_output` Docker volume).
- Async processing via Celery (queue `reports`); a dedicated
  `celery_report_worker` container handles these jobs.

Shared concerns across all services:

- **Logging:** JSON format with fields `timestamp`, `level`, `service`,
  `request_id`, `user_id`, `endpoint`, `duration_ms`, `status_code`, `message`.
- **Metrics:** `/metrics` endpoint via `prometheus-fastapi-instrumentator`.
- **Healthcheck:** `GET /health` returning `{"status":"ok","db":"ok","redis":"ok"}`
- **CORS:** strict whitelist configured per environment
- **Input validation:** Pydantic v2 strict models with type coercion disabled.

Code reuse is encouraged through a shared Python package (`common/`) containing
db sessions, base models, logging helpers, etc.

Celery workers run as separate containers with queues: `ingestion`, `ml`,
`reports`, `default`.
