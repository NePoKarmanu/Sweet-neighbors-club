from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
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
    token_response, refresh_token = signup_user(dto, db)
    response = JSONResponse(content=token_response.model_dump(), status_code=status.HTTP_201_CREATED)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/auth",
    )
    return response

