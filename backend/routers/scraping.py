from __future__ import annotations

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, Query, status

from backend.core.celery_app import celery_app
from backend.db.models.users import User
from backend.exceptions import ForbiddenAppError, NotFoundAppError, ValidationAppError
from backend.schemas.scraping import ScrapingRunResponse, ScrapingTaskStatusResponse
from backend.scrapers.base import ScraperProviderNotFoundError
from backend.scrapers.registry import list_provider_names, load_scrapers
from backend.tasks.scraping import run_all_scrapers_task
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/scraping", tags=["scraping"])


def _require_staff(current_user: User) -> None:
    if not current_user.is_staff:
        raise ForbiddenAppError("Staff access is required")


def _normalize_provider(provider: str | None) -> str | None:
    if provider is None:
        return None
    normalized = provider.strip().lower()
    if not normalized:
        raise ValidationAppError("Query parameter 'provider' cannot be empty")
    return normalized


def _validate_provider(provider: str | None) -> None:
    if provider is None:
        return
    try:
        load_scrapers(provider_name=provider)
    except ScraperProviderNotFoundError as exc:
        providers = list_provider_names()
        raise ValidationAppError(
            str(exc),
            meta={"available_providers": providers},
        ) from exc


@router.post(
    "/run",
    response_model=ScrapingRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue scraping task",
)
def run_scraping(
    provider: str | None = Query(
        default=None,
        description="Optional provider name (example: cian). If omitted, all providers are executed.",
        examples=["cian"],
    ),
    current_user: User = Depends(get_current_user),
) -> ScrapingRunResponse:
    _require_staff(current_user)
    normalized_provider = _normalize_provider(provider)
    _validate_provider(normalized_provider)

    task = run_all_scrapers_task.delay(normalized_provider)
    return ScrapingRunResponse(
        task_id=task.id,
        provider=normalized_provider,
        mode="single" if normalized_provider is not None else "all",
    )


@router.get(
    "/tasks/{task_id}",
    response_model=ScrapingTaskStatusResponse,
    summary="Get scraping task status",
)
def get_scraping_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
) -> ScrapingTaskStatusResponse:
    _require_staff(current_user)
    result = AsyncResult(task_id, app=celery_app)
    if result.state == "PENDING":
        raise NotFoundAppError("Task not found")
    payload = result.result if isinstance(result.result, dict) else None
    return ScrapingTaskStatusResponse(
        task_id=task_id,
        state=result.state,
        result=payload,
    )
