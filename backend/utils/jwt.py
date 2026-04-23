from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

from backend.db.config import (
    get_access_token_expire_minutes,
    get_jwt_algorithm,
    get_jwt_secret_key,
)


def create_access_token(user_id: int) -> str:
    expire_at = datetime.now(UTC) + timedelta(minutes=get_access_token_expire_minutes())
    payload = {"sub": str(user_id), "exp": expire_at}
    return jwt.encode(payload, get_jwt_secret_key(), algorithm=get_jwt_algorithm())


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, get_jwt_secret_key(), algorithms=[get_jwt_algorithm()])
