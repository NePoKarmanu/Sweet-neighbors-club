from __future__ import annotations

import json

from pywebpush import WebPushException, webpush

from backend.core.config import settings
from backend.db.models.push_subscriptions import PushSubscription


class PushSender:
    def send(self, *, push_subscription: PushSubscription, title: str, url: str, price: float | None) -> None:
        if not settings.WEB_PUSH_VAPID_PRIVATE_KEY or not settings.WEB_PUSH_VAPID_CLAIMS_SUBJECT:
            raise RuntimeError("Web push is not configured")

        payload = json.dumps(
            {
                "title": title,
                "body": f"Price: {price}",
                "url": url,
            }
        )
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


__all__ = ["PushSender", "WebPushException"]
