from __future__ import annotations

from collections import defaultdict
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
    filters_with_subscriptions = subscription_repository.list_active_with_subscriptions(user_id=user_id)
    subscriptions_by_user = {subscription.user_id: subscription for _, subscription in filters_with_subscriptions}
    return _materialize_deliveries_for_notifications(
        notifications=notifications,
        subscriptions_by_user=subscriptions_by_user,
        delivery_repository=delivery_repository,
        push_repository=push_repository,
        user_id=user_id,
    )


def _materialize_deliveries_for_notifications(
    *,
    notifications: list[Any],
    subscriptions_by_user: dict[int, Any],
    delivery_repository: NotificationDeliveryRepository,
    push_repository: PushSubscriptionRepository,
    user_id: int | None,
) -> int:
    created = 0
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
    commit_every = 5
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

    now = datetime.now(timezone.utc)
    grouped_deliveries = _group_deliveries(
        deliveries=deliveries,
        delivery_repository=delivery_repository,
        notification_repository=notification_repository,
        user_id=user_id,
    )

    notifications_by_id, listings_by_id, users_by_id, active_push_subscriptions_by_user_id = _build_delivery_context(
        grouped_deliveries=grouped_deliveries,
        listing_repository=listing_repository,
        user_repository=user_repository,
        push_repository=push_repository,
    )

    processed = 0
    pending_changes = 0

    for (target_user_id, channel), group in grouped_deliveries.items():
        processed_delta, pending_changes_delta = _process_delivery_group(
            group=group,
            target_user_id=target_user_id,
            channel=channel,
            now=now,
            users_by_id=users_by_id,
            listings_by_id=listings_by_id,
            active_push_subscriptions_by_user_id=active_push_subscriptions_by_user_id,
            delivery_repository=delivery_repository,
            push_repository=push_repository,
            sent_listing_repository=sent_listing_repository,
            email_sender=email_sender,
            push_sender=push_sender,
        )
        processed += processed_delta
        pending_changes += pending_changes_delta

        if pending_changes >= commit_every:
            delivery_repository.flush()
            delivery_repository.commit()
            pending_changes = 0

    if pending_changes > 0:
        delivery_repository.flush()
        delivery_repository.commit()

    return processed

def _group_deliveries(
    *,
    deliveries: list[Any],
    delivery_repository: NotificationDeliveryRepository,
    notification_repository: NotificationRepository,
    user_id: int | None,
) -> dict[tuple[int, NotificationChannel], list[Any]]:
    notification_ids = {delivery.notification_id for delivery in deliveries}
    notifications = notification_repository.get_by_ids(notification_ids=notification_ids)
    notifications_by_id = {notification.id: notification for notification in notifications}
    
    grouped_deliveries: dict[tuple[int, NotificationChannel], list[Any]] = defaultdict(list)
    for delivery in deliveries:
        notification = notifications_by_id.get(delivery.notification_id)
        if notification is None:
            delivery_repository.mark_failed(delivery=delivery, error_message="Notification is missing")
            continue
        if user_id is not None and notification.user_id != user_id:
            continue
        grouped_deliveries[(notification.user_id, delivery.channel)].append((delivery, notification))
    return grouped_deliveries

def _build_delivery_context(
    *,
    grouped_deliveries: dict[tuple[int, NotificationChannel], list[Any]],
    listing_repository: ListingRepository,
    user_repository: UserRepository,
    push_repository: PushSubscriptionRepository,
) -> tuple[dict[int, Any], dict[int, Any], dict[int, Any], dict[int, Any]]:
    notifications = [notification for group in grouped_deliveries.values() for _, notification in group]
    notifications_by_id = {notification.id: notification for notification in notifications}
    listing_ids = {notification.listing_id for notification in notifications}
    listings = listing_repository.get_by_ids(listing_ids=listing_ids)
    listings_by_id = {listing.id: listing for listing in listings}
    user_ids = {notification.user_id for notification in notifications}
    users = user_repository.get_by_ids(user_ids=user_ids)
    users_by_id = {user.id: user for user in users}
    active_push_subscriptions = push_repository.list_active_by_user_ids(user_ids=user_ids)
    active_push_subscriptions_by_user_id: dict[int, Any] = {}
    for subscription in active_push_subscriptions:
        active_push_subscriptions_by_user_id.setdefault(subscription.user_id, subscription)
    return notifications_by_id, listings_by_id, users_by_id, active_push_subscriptions_by_user_id

def _process_delivery_group(
    *,
    group: list[Any],
    target_user_id: int,
    channel: NotificationChannel,
    now: datetime,
    users_by_id: dict[int, Any],
    listings_by_id: dict[int, Any],
    active_push_subscriptions_by_user_id: dict[int, Any],
    delivery_repository: NotificationDeliveryRepository,
    push_repository: PushSubscriptionRepository,
    sent_listing_repository: SentListingRepository,
    email_sender: EmailSender,
    push_sender: PushSender,
) -> tuple[int, int]:
    processed = 0
    pending_changes = 0
    failed_push_endpoint: str | None = None
    try:
        user = users_by_id.get(target_user_id)
        if user is None:
            return _mark_group_failed(group=group, delivery_repository=delivery_repository, error_message="User is missing")

        listings_payload = _collect_listings_payload(group=group, listings_by_id=listings_by_id)
        if listings_payload is None:
            return _mark_group_failed(group=group, delivery_repository=delivery_repository, error_message="Listing is missing")

        listing_messages = [(title, url, price) for title, url, price, _ in listings_payload]
        if channel == NotificationChannel.email:
            email_sender.send_many(recipient=user.email, listings=listing_messages)
        else:
            push_subscription = active_push_subscriptions_by_user_id.get(user.id)
            if push_subscription is None:
                raise RuntimeError("No active push subscription")
            failed_push_endpoint = push_subscription.endpoint
            push_sender.send_many(push_subscription=push_subscription, listings=listing_messages)

        for delivery, _ in group:
            delivery_repository.mark_sent(delivery=delivery, sent_at=now)
            processed += 1
            pending_changes += 1
        for _, _, _, listing_id in listings_payload:
            sent_listing_repository.create_if_missing(user_id=user.id, listing_id=listing_id, sent_at=now)
            pending_changes += 1
    except WebPushException as exc:
        delivery_repository.rollback()
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        if status_code in {404, 410} and failed_push_endpoint is not None:
            push_repository.deactivate_by_endpoint(endpoint=failed_push_endpoint)
        processed_delta, pending_changes_delta = _mark_group_failed(
            group=group,
            delivery_repository=delivery_repository,
            error_message=str(exc),
        )
        processed += processed_delta
        pending_changes += pending_changes_delta
    except Exception as exc:
        processed_delta, pending_changes_delta = _mark_group_failed(
            group=group,
            delivery_repository=delivery_repository,
            error_message=str(exc),
        )
        processed += processed_delta
        pending_changes += pending_changes_delta
    return processed, pending_changes


def _collect_listings_payload(*, group: list[Any], listings_by_id: dict[int, Any]) -> list[tuple[str, str, float | None, int]] | None:
    listings_payload: list[tuple[str, str, float | None, int]] = []
    for _, notification in group:
        listing = listings_by_id.get(notification.listing_id)
        if listing is None:
            return None
        listings_payload.append(
            (listing.title, listing.url, float(listing.price) if listing.price is not None else None, listing.id)
        )
    return listings_payload

def _mark_group_failed(*, group: list[Any], delivery_repository: NotificationDeliveryRepository, error_message: str) -> tuple[int, int]:
    processed = 0
    pending_changes = 0
    for delivery, _ in group:
        delivery_repository.mark_failed(delivery=delivery, error_message=error_message)
        processed += 1
        pending_changes += 1
    return processed, pending_changes
