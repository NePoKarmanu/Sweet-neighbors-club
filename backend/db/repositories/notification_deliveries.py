from backend.db.models.notification_deliveries import NotificationDelivery
from backend.db.repositories.base import BaseRepository


class NotificationDeliveryRepository(BaseRepository[NotificationDelivery]):
    model = NotificationDelivery
