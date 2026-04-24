from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.models.users import User
from backend.db.session import get_db
from backend.dto.auth import UpdateProfileDTO
from backend.schemas.auth import UpdateProfileRequest, UserResponse
from backend.services.profile import update_profile_user
from backend.utils.auth import get_current_user

router = APIRouter()


@router.put("/profile", response_model=UserResponse)
def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    dto = UpdateProfileDTO(
        current_password=payload.current_password,
        email=payload.email,
        phone=payload.phone,
        password=payload.password,
    )
    return update_profile_user(data=dto, current_user=current_user, db=db)
