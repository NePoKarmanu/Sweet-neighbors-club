from __future__ import annotations

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.core.celery_app import celery_app
from backend.db.models.users import User
from backend.db.session import get_db
from backend.dto.notifications import NotificationSettingsDTO, PushSubscriptionDTO
from backend.exceptions import ForbiddenAppError, NotFoundAppError, ValidationAppError
from backend.schemas.notifications import (
    NotificationPipelineRunResponse,
    NotificationPipelineTaskStatusResponse,
    NotificationSettingsRequest,
    NotificationSettingsResponse,
    PushSubscriptionRequest,
    PushSubscriptionResponse,
)
from backend.services.notifications import (
    create_notification_settings,
    delete_push_subscription,
    register_push_subscription,
)
from backend.tasks.notifications import run_full_pipeline_task
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _require_staff(current_user: User) -> None:
    if not current_user.is_staff:
        raise ForbiddenAppError("Staff access is required")


@router.post("", response_model=NotificationSettingsResponse, status_code=status.HTTP_201_CREATED)
def create_notifications_settings(
    payload: NotificationSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationSettingsResponse:
    try:
        dto = NotificationSettingsDTO.model_validate(payload.model_dump())
    except ValidationError as exc:
        raise ValidationAppError(str(exc)) from exc
    return create_notification_settings(db=db, current_user=current_user, payload=dto)


@router.post("/push-subscriptions", response_model=PushSubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_push_subscription(
    payload: PushSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PushSubscriptionResponse:
    dto = PushSubscriptionDTO.model_validate(payload.model_dump())
    entity = register_push_subscription(db=db, current_user=current_user, payload=dto)
    return PushSubscriptionResponse.model_validate(entity)


@router.delete("/push-subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_push_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    delete_push_subscription(db=db, current_user=current_user, subscription_id=subscription_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/admin/run",
    response_model=NotificationPipelineRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue full notifications pipeline task",
)
def run_notifications_pipeline(
    user_id: int | None = Query(
        default=None,
        ge=1,
        description="Optional user id. If omitted, runs for all users.",
    ),
    current_user: User = Depends(get_current_user),
) -> NotificationPipelineRunResponse:
    _require_staff(current_user)
    task = run_full_pipeline_task.delay(user_id)
    return NotificationPipelineRunResponse(task_id=task.id, mode="full", user_id=user_id)


@router.get(
    "/admin/tasks/{task_id}",
    response_model=NotificationPipelineTaskStatusResponse,
    summary="Get notifications pipeline task status",
)
def get_notifications_pipeline_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
) -> NotificationPipelineTaskStatusResponse:
    _require_staff(current_user)
    result = AsyncResult(task_id, app=celery_app)
    if result.state == "PENDING":
        raise NotFoundAppError("Task not found")
    payload = result.result if isinstance(result.result, dict) else None
    return NotificationPipelineTaskStatusResponse(
        task_id=task_id,
        state=result.state,
        result=payload,
    )
