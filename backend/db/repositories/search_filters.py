from backend.db.models.search_filters import SearchFilter
from backend.db.repositories.base import BaseRepository


class SearchFilterRepository(BaseRepository[SearchFilter]):
    model = SearchFilter
