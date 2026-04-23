from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.dto.auth import SigninDTO
from backend.schemas.auth import SigninRequest, TokenResponse
from backend.services.signin import signin_user

router = APIRouter()


@router.post("/signin", response_model=TokenResponse)
def signin(payload: SigninRequest, db: Session = Depends(get_db)) -> TokenResponse:
    dto = SigninDTO(email=payload.email, password=payload.password)
    return signin_user(dto, db)
