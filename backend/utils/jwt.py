from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging

import jwt

from backend.core.security import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET

logger = logging.getLogger(__name__)


def warn_if_weak_jwt_secret() -> None:
    if JWT_ALGORITHM != "HS256":
        return
    key_length = len(JWT_SECRET.encode("utf-8"))
    if key_length < 32:
        logger.warning(
            "JWT secret is %s bytes; at least 32 bytes is recommended for HS256 (RFC 7518 Section 3.2)",
            key_length,
        )


def create_access_token(user_id: int) -> str:
    expire_at = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire_at}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
