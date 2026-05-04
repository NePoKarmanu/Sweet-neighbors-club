from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from backend.db.models.sent_listings import SentListing
from backend.db.repositories.base import BaseRepository


class SentListingRepository(BaseRepository[SentListing]):
    model = SentListing

    def create_if_missing(self, *, user_id: int, listing_id: int, sent_at: datetime) -> SentListing:
        query = select(SentListing).where(
            SentListing.user_id == user_id,
            SentListing.listing_id == listing_id,
        )
        entity = self.session.scalar(query)
        if entity is None:
            entity = SentListing(user_id=user_id, listing_id=listing_id, sent_at=sent_at)
            self.session.add(entity)
            self.session.flush()
            self.session.refresh(entity)
        return entity
