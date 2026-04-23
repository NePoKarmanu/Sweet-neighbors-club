from fastapi import APIRouter, Depends

from backend.db.models.users import User
from backend.schemas.auth import MessageResponse
from backend.services.exit import exit_user
from backend.utils.auth import get_current_user

router = APIRouter()


@router.post("/exit", response_model=MessageResponse)
def logout(current_user: User = Depends(get_current_user)) -> MessageResponse:
    return exit_user(current_user)
