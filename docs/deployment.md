# Deployment & CI/CD

Covers Docker build strategy, GitHub Actions pipeline, zero-downtime deploy
and backup procedures.

## 10.1 Docker Build Strategy

- Multi-stage Dockerfiles per service:
  - Stage 1 (builder): install dependencies, run tests, compile assets
  - Stage 2 (runtime): minimal base image with only artifacts
- Python services use `python:3.11-slim-bookworm`.
- Node services use `node:20-alpine`.
- Use non-root user (uid 1000) in final images.
- `.dockerignore` excludes `.git`, `__pycache__`, `.env`, `node_modules`,
  `tests`, `docs`.
- Images are tagged `service:semver-gitSHA`.
- Pin base image digests in production.
- Define `HEALTHCHECK` in every Dockerfile.

## 10.2 CI/CD Pipeline (GitHub Actions)

- Workflow jobs:
  1. `lint` – run Python and JS linters, markdown linter
  2. `test` – execute unit and integration tests in parallel across services
  3. `build` – build Docker images using BuildKit, cache layers
  4. `push` – push to registry with semantic tag for staging/production
  5. `deploy` – run `docker compose` on target host via SSH (or use
     self-hosted runner)
- Build once, deploy to both staging and production by retagging.
- Enforce branch protection rules, require passing checks.

## 10.3 Zero-Downtime Deployment

- Deploy services one at a time with `docker compose up -d --no-deps <service>`.
- Nginx upstream has two replicas per FastAPI service; rolling restart keeps
  at least one instance serving.
- Run Alembic migrations before restarting the service.  Migrations must be
  backward-compatible (additive only).
- Health check grace period: 30 s after container start before traffic is
  routed.

## 10.4 Backup Strategy

- PostgreSQL: daily `pg_dump` at 01:00 PST, gzip-compressed, stored to
  local volume and `rsync` to offsite storage. Retention: 30-day dailies,
  12-monthly snapshots.
- Redis: AOF persistence enabled; RDB snapshot every 15 minutes.
- Model artifacts: versioned in `model_store` volume; retain 6 months.
- Meilisearch: weekly export snapshots to backup volume.
- Scripts and instructions stored in `docs/operating.md`.
