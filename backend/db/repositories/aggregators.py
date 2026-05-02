from backend.db.models.aggregators import Aggregator
from backend.db.repositories.base import BaseRepository


class AggregatorRepository(BaseRepository[Aggregator]):
    model = Aggregator

    def get_or_create(self, *, name: str, base_url: str) -> Aggregator:
        aggregator = self.get_one_by(name=name)
        if aggregator is not None:
            if aggregator.base_url != base_url:
                aggregator.base_url = base_url
                self.session.commit()
                self.session.refresh(aggregator)
            return aggregator

        return self.create(name=name, base_url=base_url)
