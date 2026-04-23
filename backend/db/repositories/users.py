from backend.db.models.users import User
from backend.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User
