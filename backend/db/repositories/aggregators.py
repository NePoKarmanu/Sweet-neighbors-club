from backend.db.models.aggregators import Aggregator
from backend.db.repositories.base import BaseRepository


class AggregatorRepository(BaseRepository[Aggregator]):
    model = Aggregator
