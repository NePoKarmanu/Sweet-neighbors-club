from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.db.repositories.users import UserRepository
from backend.dto.auth import SigninDTO
from backend.schemas.auth import TokenResponse, UserResponse
from backend.utils.jwt import create_access_token
from backend.utils.security import verify_password


def signin_user(data: SigninDTO, db: Session) -> TokenResponse:
    user = UserRepository(db).get_by_email(data.email)

    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserResponse.model_validate(user),
    )
