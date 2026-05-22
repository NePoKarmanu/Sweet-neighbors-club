from __future__ import annotations

import json
import logging

from pywebpush import WebPushException, webpush

from backend.core.config import settings
from backend.db.models.push_subscriptions import PushSubscription
from backend.logging_utils import log_exception, log_info

logger = logging.getLogger(__name__)


class PushSender:
    def send(
        self,
        *,
        push_subscription: PushSubscription,
        title: str,
        url: str,
        price: float | None,
        user_id: int | None = None,
    ) -> None:
        self.send_many(
            push_subscription=push_subscription,
            listings=[(title, url, price)],
            user_id=user_id,
        )
    
    def send_many(
        self,
        *,
        push_subscription: PushSubscription,
        listings: list[tuple[str, str, float | None]],
        user_id: int | None = None,
    ) -> None:
        log_info(
            logger, "Push send attempt started", event="notifications.push_send_attempt",
            channel="push", user_id=user_id, listings_count=len(listings)
        )
        if not settings.WEB_PUSH_VAPID_PRIVATE_KEY or not settings.WEB_PUSH_VAPID_CLAIMS_SUBJECT:
            raise RuntimeError("Web push is not configured")
        if not listings:
            raise RuntimeError("No listings to send")

        first_url = listings[0][1]
        payload = json.dumps(
            {
                "title": "Новые объявления",
                "body": "Появились новые объявления, проверьте почту",
                "url": first_url,
            }
        )
        try:
            webpush(
                subscription_info={
                    "endpoint": push_subscription.endpoint,
                    "keys": {
                        "p256dh": push_subscription.p256dh,
                        "auth": push_subscription.auth,
                    },
                },
                data=payload,
                vapid_private_key=settings.WEB_PUSH_VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.WEB_PUSH_VAPID_CLAIMS_SUBJECT},
            )
            log_info(
                logger, "Push send attempt succeeded", event="notifications.push_send_success",
                channel="push", user_id=user_id, listings_count=len(listings)
            )
        except Exception:
            log_exception(
                logger, "Push send attempt failed", event="notifications.push_send_failed",
                channel="push", user_id=user_id
            )
            raise


__all__ = ["PushSender", "WebPushException"]
