from backend.db.models.sent_listings import SentListing
from backend.db.repositories.base import BaseRepository


class SentListingRepository(BaseRepository[SentListing]):
    model = SentListing
