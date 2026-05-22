from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.dto.auth import SigninDTO
from backend.schemas.auth import SigninRequest, TokenResponse
from backend.services.signin import signin_user

router = APIRouter()


@router.post("/signin", response_model=TokenResponse)
def signin(payload: SigninRequest, db: Session = Depends(get_db)) -> TokenResponse:
    dto = SigninDTO(email=payload.email, password=payload.password)
    token_response, refresh_token = signin_user(dto, db)
    response = JSONResponse(content=token_response.model_dump())
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/auth",
    )
    return response

