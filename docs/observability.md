# Observability & Monitoring

Covers metrics, logging, dashboards, alerting, and health‑check policies.

## 8.1 Metrics — Prometheus + Grafana

- Every FastAPI service exposes `/metrics` using
  `prometheus-fastapi-instrumentator`.
- Celery worker metrics via `celery-prometheus-exporter`.
- Business metrics pushed with `prometheus_client` counters/histograms.

### 8.1.1 Custom Business Metrics

- `ingestion_records_total` by source
- `arv_requests_total` and `arv_latency_seconds`
- `model_mape` per model version
- `reports_generated_total` (incremented when a report task completes)

### 8.1.2 Grafana Dashboards

1. System Overview: CPU/memory/disk/network per container (via cAdvisor)
2. API Performance: request rate, error rate, p50/p95/p99 latency
3. Data Pipeline: ingestion success rate, records/min, queue depth
4. ML Model Health: MAPE trend, prediction latency, model version
5. Celery Workers: throughput, queue depth, failure rate
6. Database: query latency, connection pool utilization
7. Business KPIs: daily active users, searches/day, reports/day, ARV
   requests

## 8.2 Logging — Loki + Promtail

- Containers log JSON to stdout/stderr.
- Promtail sidecar collects logs and ships to Loki.
- Grafana provides a search UI via the Loki datasource.
- Retention: 90 days.

Structured log format example:

```json
{"timestamp":"2026-02-26T12:00:00Z","level":"INFO","service":"property_service","request_id":"...","user_id":"...","endpoint":"/properties/search","duration_ms":45,"status_code":200,"message":"Search completed"}
```

## 8.3 Alerting

Prometheus Alertmanager sends to a webhook (Gotify/SNMP/SMTP).  Rules include:

- Service down (>2 min unhealthy)
- High error rate (>5% 5xx over 5 min)
- Slow API (p95 > 2 s for >5 min)
- Model degradation (MAPE > 12%)
- Ingestion failure (2+ consecutive task failures)
- Disk > 80% capacity
- PgBouncer pool exhaustion

## 8.4 Health Checks

- Docker `HEALTHCHECK` directives for every container.
- FastAPI `/health` returning status for DB, Redis, dependencies.
- Compose `depends_on` with `condition: service_healthy` ensures startup
  ordering; Nginx upstream health checks remove unhealthy backends
  automatically.
