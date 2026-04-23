from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.dto.auth import SignupDTO
from backend.schemas.auth import SignupRequest, TokenResponse
from backend.services.signup import signup_user

router = APIRouter()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    dto = SignupDTO(
        email=payload.email,
        phone=payload.phone,
        password=payload.password,
    )
    return signup_user(dto, db)
