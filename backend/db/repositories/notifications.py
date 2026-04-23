from backend.db.models.notifications import Notification
from backend.db.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    model = Notification
