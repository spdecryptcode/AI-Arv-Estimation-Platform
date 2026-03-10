from celery import Celery
import os

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery = Celery(
    "arv",
    broker=redis_url,
    backend=redis_url,
)

# auto-discover tasks in all installed apps or specified modules
# include ml_service tasks and any others under services
celery.autodiscover_tasks([
    "common.tasks",
    "services.ml_service.app.tasks",
    "services.report_service.app.tasks",
])

# example configuration
celery.conf.task_routes = {
    # tasks can be routed here if needed
}

from celery.schedules import crontab

# schedule periodic retraining; cron string configurable via RETRAIN_CRON
# default to daily at midnight UTC
cron_expr = os.getenv("RETRAIN_CRON", "0 0 * * *")
# celery crontab accepts fields hour/minute/day/month/weekday; we parse
fields = cron_expr.split()
if len(fields) != 5:
    raise ValueError(f"invalid RETRAIN_CRON format: {cron_expr}")
minute, hour, day_of_month, month, day_of_week = fields
celery.conf.beat_schedule = {
    "retrain-models": {
        "task": "services.ml_service.app.tasks.retrain_models",
        "schedule": crontab(minute=minute, hour=hour, day_of_month=day_of_month, month_of_year=month, day_of_week=day_of_week),
    },
}
