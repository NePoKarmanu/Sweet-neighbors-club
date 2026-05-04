from __future__ import annotations

from datetime import date

from sqlalchemy import select

from backend.db.models.subscriptions import Subscription
from backend.db.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    model = Subscription

    def get_active_by_user_id(self, *, user_id: int) -> Subscription | None:
        query = select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.deleted_at.is_(None),
        )
        return self.session.scalar(query)

    def upsert_for_user(
        self,
        *,
        user_id: int,
        start_date: date,
        end_date: date,
        notify_email: bool,
        notify_push: bool,
        is_active: bool,
    ) -> Subscription:
        entity = self.get_active_by_user_id(user_id=user_id)
        if entity is None:
            entity = Subscription(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                notify_email=notify_email,
                notify_push=notify_push,
                is_active=is_active,
            )
            self.session.add(entity)
        else:
            entity.start_date = start_date
            entity.end_date = end_date
            entity.notify_email = notify_email
            entity.notify_push = notify_push
            entity.is_active = is_active
            entity.deleted_at = None
        self.session.commit()
        self.session.refresh(entity)
        return entity
