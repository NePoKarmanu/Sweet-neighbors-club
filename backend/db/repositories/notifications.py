from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select

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
        query = select(Notification).where(
            Notification.user_id == user_id,
            Notification.listing_id == listing_id,
        )
        entity = self.session.scalar(query)
        if entity is None:
            entity = Notification(user_id=user_id, listing_id=listing_id)
            self.session.add(entity)
            self.session.flush()
            self.session.refresh(entity)
            return entity
        return None

    def list_unprocessed(self, *, limit: int) -> list[Notification]:
        query = (
            select(Notification)
            .where(Notification.deleted_at.is_(None))
            .order_by(Notification.id.asc())
            .limit(limit)
        )
        return list(self.session.scalars(query))
