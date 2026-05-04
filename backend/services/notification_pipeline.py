from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.db.models.enums import NotificationChannel
from backend.db.models.search_filters import SearchFilter
from backend.db.models.subscriptions import Subscription
from backend.db.repositories.listings import ListingRepository
from backend.db.repositories.notification_deliveries import NotificationDeliveryRepository
from backend.db.repositories.notifications import NotificationRepository
from backend.db.repositories.push_subscriptions import PushSubscriptionRepository
from backend.db.repositories.search_filters import SearchFilterRepository
from backend.db.repositories.sent_listings import SentListingRepository
from backend.db.repositories.users import UserRepository
from backend.services.deliveries.email_sender import EmailSender
from backend.services.deliveries.push_sender import PushSender, WebPushException


def _fits_range(value: float | int | None, minimum: float | int | None, maximum: float | int | None) -> bool:
    """Check value against optional bounds.

    `None` bounds are treated as unbounded limits.
    """
    if minimum is not None and (value is None or value < minimum):
        return False
    if maximum is not None and (value is None or value > maximum):
        return False
    return True


def _matches_listing(search_filter: SearchFilter, listing_data: dict[str, Any]) -> bool:
    if not _fits_range(listing_data.get("price"), search_filter.price_min, search_filter.price_max):
        return False
    if not _fits_range(listing_data.get("rooms"), search_filter.rooms_min, search_filter.rooms_max):
        return False
    if not _fits_range(listing_data.get("area"), search_filter.area_min, search_filter.area_max):
        return False
    if not _fits_range(listing_data.get("floor"), search_filter.floor_min, search_filter.floor_max):
        return False

    params: dict[str, Any] = search_filter.additional_params or {}
    details: dict[str, Any] = listing_data.get("details", {})
    if search_filter.city:
        listing_city = listing_data.get("city")
        if not isinstance(listing_city, str):
            return False
        if listing_city.casefold() != search_filter.city.casefold():
            return False

    property_types = params.get("property_types") or []
    if property_types and details.get("property_type") not in property_types:
        return False

    creator_types = params.get("creator_types") or []
    if creator_types and details.get("creator_type") not in creator_types:
        return False

    living_conditions = params.get("living_conditions") or []
    if living_conditions:
        current_conditions = details.get("living_conditions") or []
        if not all(condition in current_conditions for condition in living_conditions):
            return False

    has_repair = params.get("has_repair")
    if has_repair is not None and details.get("has_repair") is not has_repair:
        return False

    build_year_filter = params.get("build_year") or {}
    if isinstance(build_year_filter, dict):
        if not _fits_range(
            details.get("build_year"),
            build_year_filter.get("min"),
            build_year_filter.get("max"),
        ):
            return False

    return True


def match_listings_to_subscriptions(
    db: Session,
    *,
    batch_size: int,
    user_id: int | None = None,
) -> int:
    listing_repository = ListingRepository(db)
    filter_repository = SearchFilterRepository(db)
    notification_repository = NotificationRepository(db)

    listings = listing_repository.list_recent_active(limit=batch_size)
    if not listings:
        return 0

    filters_with_subscriptions = filter_repository.list_active_with_subscriptions(user_id=user_id)
    created = 0
    for listing in listings:
        listing_payload = {
            "price": listing.price,
            "rooms": listing.rooms,
            "area": listing.area,
            "floor": listing.floor,
            "city": listing.city or (listing.data or {}).get("city"),
            "details": listing.data or {},
        }
        for search_filter, subscription in filters_with_subscriptions:
            if not isinstance(subscription, Subscription):
                continue
            if not _matches_listing(search_filter, listing_payload):
                continue
            existing = notification_repository.create_if_missing(
                user_id=subscription.user_id,
                listing_id=listing.id,
            )
            if existing is not None:
                created += 1
    return created


def materialize_pending_deliveries(
    db: Session,
    *,
    batch_size: int,
    user_id: int | None = None,
) -> int:
    notification_repository = NotificationRepository(db)
    subscription_repository = SearchFilterRepository(db)
    delivery_repository = NotificationDeliveryRepository(db)
    push_repository = PushSubscriptionRepository(db)

    notifications = notification_repository.list_unprocessed(limit=batch_size)
    created = 0
    filters_with_subscriptions = subscription_repository.list_active_with_subscriptions(user_id=user_id)
    subscriptions_by_user = {subscription.user_id: subscription for _, subscription in filters_with_subscriptions}
    for notification in notifications:
        if user_id is not None and notification.user_id != user_id:
            continue
        subscription = subscriptions_by_user.get(notification.user_id)
        if subscription is None:
            continue
        has_active_push_subscription = push_repository.get_any_active_for_user(
            user_id=notification.user_id
        ) is not None
        created += delivery_repository.materialize_channels_for_notification(
            notification_id=notification.id,
            include_email=subscription.notify_email,
            include_push=subscription.notify_push and has_active_push_subscription,
        )
    return created


def process_pending_deliveries(
    db: Session,
    *,
    batch_size: int,
    user_id: int | None = None,
) -> int:
    delivery_repository = NotificationDeliveryRepository(db)
    notification_repository = NotificationRepository(db)
    listing_repository = ListingRepository(db)
    user_repository = UserRepository(db)
    push_repository = PushSubscriptionRepository(db)
    sent_listing_repository = SentListingRepository(db)
    email_sender = EmailSender()
    push_sender = PushSender()

    deliveries = delivery_repository.list_pending(limit=batch_size)
    if not deliveries:
        return 0

    processed = 0
    now = datetime.now(timezone.utc)
    for delivery in deliveries:
        notification = notification_repository.get_by_id(delivery.notification_id)
        if notification is None:
            delivery_repository.mark_failed(delivery=delivery, error_message="Notification is missing")
            processed += 1
            continue
        if user_id is not None and notification.user_id != user_id:
            continue

        listing = listing_repository.get_by_id(notification.listing_id)
        user = user_repository.get_by_id(notification.user_id)
        if listing is None or user is None:
            delivery_repository.mark_failed(delivery=delivery, error_message="Listing or user is missing")
            processed += 1
            continue

        try:
            failed_push_endpoint: str | None = None
            if delivery.channel == NotificationChannel.email:
                email_sender.send(
                    recipient=user.email,
                    title=listing.title,
                    url=listing.url,
                    price=float(listing.price) if listing.price is not None else None,
                )
            else:
                push_subscription = push_repository.get_any_active_for_user(user_id=user.id)
                if push_subscription is None:
                    raise RuntimeError("No active push subscription")
                failed_push_endpoint = push_subscription.endpoint
                push_sender.send(
                    push_subscription=push_subscription,
                    title=listing.title,
                    url=listing.url,
                    price=float(listing.price) if listing.price is not None else None,
                )

            delivery_repository.mark_sent(delivery=delivery, sent_at=now)
            sent_listing_repository.create_if_missing(
                user_id=user.id,
                listing_id=listing.id,
                sent_at=now,
            )
        except WebPushException as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code in {404, 410} and failed_push_endpoint is not None:
                push_repository.deactivate_by_endpoint(endpoint=failed_push_endpoint)
            delivery_repository.mark_failed(delivery=delivery, error_message=str(exc))
        except Exception as exc:
            delivery_repository.mark_failed(delivery=delivery, error_message=str(exc))

        processed += 1

    return processed
