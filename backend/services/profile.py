from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.db.models.users import User
from backend.db.repositories.users import UserRepository
from backend.dto.auth import UpdateProfileDTO
from backend.schemas.auth import UserResponse
from backend.utils.security import hash_password, verify_password


def update_profile_user(*, data: UpdateProfileDTO, current_user: User, db: Session) -> UserResponse:
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password",
        )

    users = UserRepository(db)

    if data.email is not None and data.email != current_user.email:
        existing_user_by_email = users.get_by_email(data.email)
        if existing_user_by_email is not None and existing_user_by_email.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )
        current_user.email = data.email

    if data.phone is not None and data.phone != current_user.phone:
        existing_user_by_phone = users.get_by_phone(data.phone)
        if existing_user_by_phone is not None and existing_user_by_phone.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this phone already exists",
            )
        current_user.phone = data.phone

    if data.password:
        current_user.password_hash = hash_password(data.password)

    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)
