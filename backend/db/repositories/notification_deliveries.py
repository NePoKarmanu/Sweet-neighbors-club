from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

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
        existing_channels = {
            row[0]
            for row in self.session.execute(
                select(NotificationDelivery.channel).where(
                    NotificationDelivery.notification_id == notification_id,
                    NotificationDelivery.deleted_at.is_(None),
                )
            ).all()
        }
        created = 0
        if include_email and NotificationChannel.email not in existing_channels:
            self.session.add(
                NotificationDelivery(
                    notification_id=notification_id,
                    channel=NotificationChannel.email,
                    status=DeliveryStatus.pending,
                )
            )
            created += 1
        if include_push and NotificationChannel.push not in existing_channels:
            self.session.add(
                NotificationDelivery(
                    notification_id=notification_id,
                    channel=NotificationChannel.push,
                    status=DeliveryStatus.pending,
                )
            )
            created += 1
        if created:
            self.session.commit()
        return created

    def mark_sent(self, *, delivery: NotificationDelivery, sent_at: datetime) -> None:
        delivery.status = DeliveryStatus.sent
        delivery.sent_at = sent_at
        delivery.error_message = None
        self.session.commit()

    def mark_failed(self, *, delivery: NotificationDelivery, error_message: str) -> None:
        delivery.status = DeliveryStatus.failed
        delivery.error_message = error_message
        self.session.commit()
