from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select

from backend.db.models.search_filters import SearchFilter
from backend.db.models.subscriptions import Subscription
from backend.db.repositories.base import BaseRepository


class SearchFilterRepository(BaseRepository[SearchFilter]):
    model = SearchFilter

    def get_by_subscription_id(self, *, subscription_id: int) -> SearchFilter | None:
        query = select(SearchFilter).where(
            SearchFilter.subscription_id == subscription_id,
            SearchFilter.deleted_at.is_(None),
        )
        return self.session.scalar(query)

    def upsert_for_subscription(self, *, subscription_id: int, payload: dict[str, Any]) -> SearchFilter:
        entity = self.get_by_subscription_id(subscription_id=subscription_id)
        if entity is None:
            entity = SearchFilter(subscription_id=subscription_id, **payload)
            self.session.add(entity)
        else:
            for key, value in payload.items():
                setattr(entity, key, value)
            entity.deleted_at = None
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def list_active_with_subscriptions(
        self,
        *,
        user_id: int | None = None,
    ) -> list[tuple[SearchFilter, Subscription]]:
        today = date.today()
        query = (
            select(SearchFilter, Subscription)
            .join(Subscription, Subscription.id == SearchFilter.subscription_id)
            .where(
                SearchFilter.deleted_at.is_(None),
                Subscription.deleted_at.is_(None),
                Subscription.is_active.is_(True),
                Subscription.start_date <= today,
                Subscription.end_date >= today,
            )
        )
        if user_id is not None:
            query = query.where(Subscription.user_id == user_id)
        return [(row[0], row[1]) for row in self.session.execute(query).all()]
