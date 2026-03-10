# Operating Guide

Runbook and procedures for running the system in production.

## Deploying a Release

1. Push commits and open a PR; wait for CI to succeed.
2. Merge to `main`; GitHub Actions will build and tag images.
3. SSH to the production host and pull images:
   ```bash
   docker compose pull
   ```
4. Run database migrations:
   ```bash
   docker compose run --rm auth_service alembic upgrade head
   ```
5. Deploy each service in turn:
   ```bash
   docker compose up -d --no-deps property_service
   docker compose up -d --no-deps ml_service
   # etc.
   ```
6. Verify health endpoints and Prometheus metrics; watch Grafana dashboards.

## Backups

- **PostgreSQL:**
  ```bash
  docker compose exec postgres pg_dump -U $POSTGRES_USER -d
  $POSTGRES_DB | gzip > /backups/pg-$(date +%F).sql.gz
  rsync -av /backups/ user@offsite:/path/
  ```
  A cron job runs nightly; retention is managed by `find -mtime`.

- **Redis:** AOF is enabled; RDB snapshots every 15 min are in
  `/data/redis`.  Periodically copy to offsite storage.

- **Meilisearch:** weekly snapshot script:
  ```bash
  docker compose exec meilisearch meilisearch --export /backups/meili-$(date
  +%F)
  ```

- **Model Artifacts:** archived in `/model_store` with date prefixes.

## Monitoring & Alerts

- Respond to Alertmanager webhook notifications (Gotify/email).
- Use Grafana dashboards to triage performance issues.
- Logs are searchable via Loki; use `service=<name>` filters.

## Common Tasks

- Restart a misbehaving service:
  ```bash
  docker compose restart ml_service
  ```
- Flush Redis cache:
  ```bash
  docker compose exec redis redis-cli FLUSHALL
  ```
- Manually trigger ETL ingestion:
  ```bash
  docker compose exec celery_worker celery -A app.tasks ingestion.fetch_assessor_data
  ```

## Troubleshooting

- **Database connection errors:** check PgBouncer pool and Postgres health.
- **Slow queries:** inspect `pg_stat_activity` and enable `auto_explain`.
- **High API latency:** examine Prometheus p95 metrics; check Celery queue
  depth.
- **Model degradation:** review `model_mape` dashboard and schedule retrain
  if >12%.

## Security Incidents

- Rotate JWT private key by generating a new key and updating the Docker
  secret; restart auth_service.
- Revoke tokens by flushing Redis entries for affected users.

## Contact & Support

For operational assistance, contact the on-call engineer via the team's
communication channel.  Maintain a schedule in the internal wiki.
