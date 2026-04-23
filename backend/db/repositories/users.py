from backend.db.models.users import User
from backend.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.get_one_by(email=email)

    def get_by_phone(self, phone: str) -> User | None:
        return self.get_one_by(phone=phone)
