# System Architecture

This document describes the high-level architecture of the ARV estimation
platform, including service inventory, network topology, and core Docker
configuration.

## High-Level Overview

The system follows a microservices architecture comprised of four primary
FastAPI services:

- `auth_service` – authentication and authorization (port 8001)
- `property_service` – property search, comp selection, comparison (port
  8002)
- `ml_service` – hosts ARV models and coordinates AI narrative generation
  (port 8003)
- `report_service` – generates PDF property reports asynchronously
- `celery_ml_worker` – processes ML inference jobs (configured to listen on the `ml` queue)
- `celery_ml_worker` – dedicated worker for ML inference tasks (queue `ml`)
  (port 8004)

All services communicate over a shared Docker network (`internal_net`).
Inter-service HTTP calls are made using internal Docker DNS names; no service
is exposed directly to the public internet.  Nginx acts as a reverse proxy and
TLS terminator for incoming traffic on ports 80 and 443.

### Supporting infrastructure

- PostgreSQL 15 with PostGIS 3.3 extension (shared volume)
- Redis for caching, token storage, pub/sub, Celery broker & result backend
- Meilisearch for full-text and geo-enabled property indexing
- PgBouncer for database connection pooling
- Celery workers (concurrency configurable) handling ETL, ML inference,
  report rendering
- Observability stack: Prometheus, Grafana, Loki, Promtail, cAdvisor,
  exporters, Alertmanager
- AI model host: Ollama container running Llama 3.1 (GPU passthrough or CPU)

## Docker Service Inventory

Services are grouped logically in the `docker-compose.yml` base file and
extended in override files.  Groups:

1. **Ingress:** nginx with mounted TLS certs, `nginx.conf`, and static assets
2. **Application:** frontend, auth_service, property_service, ml_service,
   report_service
3. **Data:** postgres (+PostGIS), redis, meilisearch
4. **AI:** ollama with GPU reservations; model pull script on startup
5. **Workers:** celery_worker, celery_beat (using django-celery-beat scheduler)
6. **Observability:** prometheus, grafana, loki, promtail, cadvisor,
   nginx_exporter, postgres_exporter, flower

## Network Architecture

All containers join the user-defined `internal_net`.  Only Nginx publishes
ports to the host; internal services communicate on the private subnet.

External traffic → Nginx → appropriate FastAPI service

Celery tasks and asynchronous jobs operate over Redis; the database is only
reachable internally and via PgBouncer to limit connection counts.

## Docker Compose Core Configuration

The compose configuration is split into three files:

- `docker-compose.yml` — base definition used for every environment
- `docker-compose.override.yml` — development-specific overrides (volume
  mounts, build contexts, debug tooling)
- `docker-compose.prod.yml` — production adjustments (replicas, resource
  limits, healthcheck tuning, environment-specific secrets)

Use the following command for production:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Volume strategy

Volumes are declared for persistent state:

- `postgres_data` – PostgreSQL WAL & data files
- `redis_data` – Redis AOF persistence
- `meilisearch_data` – Meilisearch index snapshots
- `model_store` – trained ML model artifacts
- `report_output` – generated PDF reports
- `nginx_certs` – TLS certificates (Let's Encrypt or self-signed)

Other ephemeral volumes mount code directories during development.

Diagrams and further details are stored under `docs/images/`.