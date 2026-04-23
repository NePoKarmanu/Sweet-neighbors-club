from backend.db.models.listings import Listing
from backend.db.repositories.base import BaseRepository


class ListingRepository(BaseRepository[Listing]):
    model = Listing
