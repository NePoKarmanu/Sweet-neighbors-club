from __future__ import annotations

from sqlalchemy.orm import Session

from backend.core.celery_app import celery_app
from backend.db.session import SessionLocal
from backend.scrapers.runner import ScrapeRunResult, run_all_scrapers


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
        result = run_all_scrapers(db, provider_name=provider_name)
        return _serialize_result(result)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
