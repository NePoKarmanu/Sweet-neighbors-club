from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from sqlalchemy import select

from backend.db.models.push_subscriptions import PushSubscription
from backend.db.repositories.base import BaseRepository


class PushSubscriptionRepository(BaseRepository[PushSubscription]):
    model = PushSubscription

    def list_active_by_user_ids(self, *, user_ids: Iterable[int]) -> list[PushSubscription]:
        ids = list(user_ids)
        if not ids:
            return []
        query = select(PushSubscription).where(
            PushSubscription.user_id.in_(ids),
            PushSubscription.is_active.is_(True),
            PushSubscription.deleted_at.is_(None),
        )
        return list(self.session.scalars(query))

    def list_active_for_user(self, *, user_id: int) -> list[PushSubscription]:
        query = select(PushSubscription).where(
            PushSubscription.user_id == user_id,
            PushSubscription.is_active.is_(True),
            PushSubscription.deleted_at.is_(None),
        )
        return list(self.session.scalars(query))

    def get_any_active_for_user(self, *, user_id: int) -> PushSubscription | None:
        query = select(PushSubscription).where(
            PushSubscription.user_id == user_id,
            PushSubscription.is_active.is_(True),
            PushSubscription.deleted_at.is_(None),
        )
        return self.session.scalar(query)

    def upsert_for_user(
        self,
        *,
        user_id: int,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: str | None,
    ) -> PushSubscription:
        query = select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        existing = self.session.scalar(query)
        now = datetime.now(timezone.utc)
        if existing is None:
            entity = PushSubscription(
                user_id=user_id,
                endpoint=endpoint,
                p256dh=p256dh,
                auth=auth,
                user_agent=user_agent,
                is_active=True,
                last_seen_at=now,
            )
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            return entity

        existing.user_id = user_id
        existing.p256dh = p256dh
        existing.auth = auth
        existing.user_agent = user_agent
        existing.is_active = True
        existing.deleted_at = None
        existing.last_seen_at = now
        self.session.commit()
        self.session.refresh(existing)
        return existing

    def deactivate_by_id_for_user(self, *, subscription_id: int, user_id: int) -> PushSubscription | None:
        entity = self.get_by_id(subscription_id)
        if entity is None or entity.deleted_at is not None or entity.user_id != user_id:
            return None
        entity.is_active = False
        entity.deleted_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def deactivate_by_endpoint(self, *, endpoint: str) -> None:
        query = select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        entity = self.session.scalar(query)
        if entity is None:
            return
        entity.is_active = False
        entity.deleted_at = datetime.now(timezone.utc)
        self.session.commit()
