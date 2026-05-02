from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from backend.core.config import settings

broker_url = settings.CELERY_BROKER_URL or settings.REDIS_URL
result_backend = settings.CELERY_RESULT_BACKEND or settings.REDIS_URL

celery_app = Celery(
    "sweet_neighbors_club",
    broker=broker_url,
    backend=result_backend,
    include=["backend.tasks.scraping"],
)

celery_app.conf.update(
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
)

if settings.SCRAPING_BEAT_ENABLED:
    celery_app.conf.beat_schedule = {
        "run-all-scrapers-every-10-minutes": {
            "task": "scraping.run_all_scrapers_task",
            "schedule": crontab(minute=f"*/{settings.SCRAPING_INTERVAL_MINUTES}"),
            "args": (None,),
        }
    }
