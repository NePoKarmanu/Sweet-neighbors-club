from backend.db.models.subscriptions import Subscription
from backend.db.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    model = Subscription
