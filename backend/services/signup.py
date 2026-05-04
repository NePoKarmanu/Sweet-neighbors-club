from __future__ import annotations

from sqlalchemy.orm import Session

from backend.db.repositories.users import UserRepository
from backend.dto.auth import SignupDTO
from backend.exceptions import ConflictAppError
from backend.schemas.auth import TokenResponse, UserResponse
from backend.utils.jwt import create_access_token
from backend.utils.security import hash_password


def signup_user(data: SignupDTO, db: Session) -> TokenResponse:
    users = UserRepository(db)

    if users.get_by_email(data.email) is not None:
        raise ConflictAppError("User with this email already exists")

    if users.get_by_phone(data.phone) is not None:
        raise ConflictAppError("User with this phone already exists")

    user = users.create(
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        is_staff=False,
    )

    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserResponse.model_validate(user),
    )
