from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from backend.db.models.push_subscriptions import PushSubscription
from backend.db.models.users import User
from backend.db.repositories.push_subscriptions import PushSubscriptionRepository
from backend.db.repositories.search_filters import SearchFilterRepository
from backend.db.repositories.subscriptions import SubscriptionRepository
from backend.dto.notifications import NotificationSettingsDTO, PushSubscriptionDTO
from backend.exceptions import ForbiddenAppError, NotFoundAppError, ValidationAppError
from backend.schemas.notifications import NotificationSettingsResponse


def _range_value(value, key: str):
    if value is None:
        return None
    return getattr(value, key)


def create_notification_settings(
    *,
    db: Session,
    current_user: User,
    payload: NotificationSettingsDTO,
) -> NotificationSettingsResponse:
    subscription_repository = SubscriptionRepository(db)
    filter_repository = SearchFilterRepository(db)

    start_date = payload.start_date or date.today()
    end_date = payload.end_date or (start_date + timedelta(days=30))
    if start_date > end_date:
        raise ValidationAppError("start_date must be less than or equal to end_date")

    subscription = subscription_repository.upsert_for_user(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        notify_email=payload.notify_email,
        notify_push=payload.notify_push,
        is_active=True,
    )

    search_filter = filter_repository.upsert_for_subscription(
        subscription_id=subscription.id,
        payload={
            "city": payload.city,
            "price_min": _range_value(payload.price, "min"),
            "price_max": _range_value(payload.price, "max"),
            "rooms_min": _range_value(payload.rooms, "min"),
            "rooms_max": _range_value(payload.rooms, "max"),
            "area_min": _range_value(payload.area, "min"),
            "area_max": _range_value(payload.area, "max"),
            "floor_min": _range_value(payload.floor, "min"),
            "floor_max": _range_value(payload.floor, "max"),
            "additional_params": {
                "property_types": payload.property_types or [],
                "creator_types": payload.creator_types or [],
                "living_conditions": payload.living_conditions or [],
                "has_repair": payload.has_repair,
                "build_year": {
                    "min": _range_value(payload.build_year, "min"),
                    "max": _range_value(payload.build_year, "max"),
                },
            },
        },
    )

    return NotificationSettingsResponse(
        subscription_id=subscription.id,
        filter_id=search_filter.id,
        notify_email=subscription.notify_email,
        notify_push=subscription.notify_push,
        is_active=subscription.is_active,
    )


def register_push_subscription(
    *,
    db: Session,
    current_user: User,
    payload: PushSubscriptionDTO,
) -> PushSubscription:
    return PushSubscriptionRepository(db).upsert_for_user(
        user_id=current_user.id,
        endpoint=payload.endpoint,
        p256dh=payload.p256dh,
        auth=payload.auth,
        user_agent=payload.user_agent,
    )


def delete_push_subscription(
    *,
    db: Session,
    current_user: User,
    subscription_id: int,
) -> None:
    repository = PushSubscriptionRepository(db)
    entity = repository.get_by_id(subscription_id)
    if entity is None or entity.deleted_at is not None:
        raise NotFoundAppError("Push subscription not found")
    deactivated = repository.deactivate_by_id_for_user(
        subscription_id=subscription_id,
        user_id=current_user.id,
    )
    if deactivated is None:
        raise ForbiddenAppError("Forbidden")
