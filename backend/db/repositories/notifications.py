from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import exists, select
from sqlalchemy.dialects.postgresql import insert

from backend.db.models.notification_deliveries import NotificationDelivery
from backend.db.models.notifications import Notification
from backend.db.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    model = Notification

    def get_by_ids(self, *, notification_ids: Iterable[int]) -> list[Notification]:
        ids = list(notification_ids)
        if not ids:
            return []
        query = select(Notification).where(Notification.id.in_(ids))
        return list(self.session.scalars(query))

    def create_if_missing(self, *, user_id: int, listing_id: int) -> Notification | None:
        stmt = (
            insert(Notification)
            .values(user_id=user_id, listing_id=listing_id)
            .on_conflict_do_nothing(constraint="uq_notifications_user_listing")
            .returning(Notification.id)
        )
        created_notification_id = self.session.scalar(stmt)
        if created_notification_id is None:
            return None
        return self.get_by_id(created_notification_id)

    def list_unprocessed(self, *, limit: int, offset: int = 0) -> list[Notification]:
        query = (
            select(Notification)
            .where(
                Notification.deleted_at.is_(None),
                ~exists(
                    select(1).where(
                        NotificationDelivery.notification_id == Notification.id,
                        NotificationDelivery.deleted_at.is_(None),
                    )
                ),
            )
            .order_by(Notification.id.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(query))
