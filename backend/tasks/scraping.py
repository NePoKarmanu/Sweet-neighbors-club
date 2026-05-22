from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from backend.core.celery_app import celery_app
from backend.db.session import SessionLocal
from backend.logging_utils import log_exception, log_info
from backend.scrapers.runner import ScrapeRunResult, run_all_scrapers

logger = logging.getLogger(__name__)


def _serialize_result(result: ScrapeRunResult) -> dict:
    return {
        "created": result.created,
        "updated": result.updated,
        "failed": result.failed,
        "requested_provider": result.requested_provider,
        "executed_providers": result.executed_providers,
        "errors": [
            {"aggregator_name": error.aggregator_name, "message": error.message}
            for error in result.errors
        ],
    }


@celery_app.task(
    bind=True,
    name="scraping.run_all_scrapers_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_all_scrapers_task(self, provider_name: str | None = None) -> dict:
    db: Session = SessionLocal()
    try:
        log_info(
            logger, "Scraping task started", event="scraping.task_started",
            task="scraping.run_all_scrapers_task", task_id=self.request.id, provider_name=provider_name
        )
        result = run_all_scrapers(db, provider_name=provider_name)
        payload = _serialize_result(result)
        log_info(
            logger, "Scraping task finished", event="scraping.task_finished",
            task="scraping.run_all_scrapers_task", task_id=self.request.id, provider_name=provider_name, **payload
        )
        return payload
    except Exception:
        log_exception(
            logger, "Scraping task failed", event="scraping.task_failed",
            task="scraping.run_all_scrapers_task", task_id=self.request.id, provider_name=provider_name
        )
        db.rollback()
        raise
    finally:
        db.close()
