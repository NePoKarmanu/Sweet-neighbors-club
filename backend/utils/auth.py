from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from backend.db.repositories.users import UserRepository
from backend.db.session import get_db
from backend.db.models.users import User
from backend.exceptions import AuthAppError
from backend.utils.jwt import decode_access_token

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError) as exc:
        raise AuthAppError("Invalid access token") from exc

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise AuthAppError("User is not authorized")

    return user
