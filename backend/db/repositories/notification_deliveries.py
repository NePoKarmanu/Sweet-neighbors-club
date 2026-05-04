from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from backend.db.models.enums import DeliveryStatus, NotificationChannel
from backend.db.models.notification_deliveries import NotificationDelivery
from backend.db.repositories.base import BaseRepository


class NotificationDeliveryRepository(BaseRepository[NotificationDelivery]):
    model = NotificationDelivery

    def list_pending(self, *, limit: int) -> list[NotificationDelivery]:
        query = (
            select(NotificationDelivery)
            .where(
                NotificationDelivery.status == DeliveryStatus.pending,
                NotificationDelivery.deleted_at.is_(None),
            )
            .order_by(NotificationDelivery.id.asc())
            .limit(limit)
        )
        return list(self.session.scalars(query))

    def materialize_channels_for_notification(
        self,
        *,
        notification_id: int,
        include_email: bool,
        include_push: bool,
    ) -> int:
        channels_to_create: list[NotificationChannel] = []
        if include_email:
            channels_to_create.append(NotificationChannel.email)
        if include_push:
            channels_to_create.append(NotificationChannel.push)

        if not channels_to_create:
            return 0

        stmt = (
            insert(NotificationDelivery)
            .values(
                [
                    {
                        "notification_id": notification_id,
                        "channel": channel,
                        "status": DeliveryStatus.pending,
                    }
                    for channel in channels_to_create
                ]
            )
            .on_conflict_do_nothing(constraint="uq_notification_deliveries_notification_channel")
            .returning(NotificationDelivery.id)
        )
        inserted_ids = self.session.scalars(stmt)
        created = 0
        for _ in inserted_ids:
            created += 1
        return created

    def mark_sent(self, *, delivery: NotificationDelivery, sent_at: datetime) -> None:
        delivery.status = DeliveryStatus.sent
        delivery.sent_at = sent_at
        delivery.error_message = None

    def mark_failed(self, *, delivery: NotificationDelivery, error_message: str) -> None:
        delivery.status = DeliveryStatus.failed
        delivery.error_message = error_message
