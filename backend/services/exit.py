from __future__ import annotations

from backend.db.models.users import User
from backend.schemas.auth import MessageResponse


def exit_user(user: User) -> MessageResponse:
    return MessageResponse(detail=f"User {user.id} signed out")
