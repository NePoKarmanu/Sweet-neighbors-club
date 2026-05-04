from __future__ import annotations

from sqlalchemy.orm import Session

from backend.db.repositories.users import UserRepository
from backend.dto.auth import RefreshDTO, SigninDTO
from backend.exceptions import AuthAppError
from backend.schemas.auth import RefreshTokenResponse, TokenResponse, UserResponse
from backend.utils.jwt import create_access_token, create_refresh_token, decode_refresh_token
from jwt import InvalidTokenError
from backend.utils.security import verify_password


def signin_user(data: SigninDTO, db: Session) -> TokenResponse:
    user = UserRepository(db).get_by_email(data.email)

    if user is None or not verify_password(data.password, user.password_hash):
        raise AuthAppError("Invalid email or password")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserResponse.model_validate(user),
    )

def refresh_access_token(data: RefreshDTO) -> RefreshTokenResponse:
    try:
        payload = decode_refresh_token(data.refresh_token)
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError) as exc:
        raise AuthAppError("Invalid refresh token") from exc

    return RefreshTokenResponse(access_token=create_access_token(user_id))
