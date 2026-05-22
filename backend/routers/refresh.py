from fastapi import APIRouter, Cookie

from backend.dto.auth import RefreshDTO
from backend.schemas.auth import RefreshTokenResponse
from backend.services.signin import refresh_access_token

router = APIRouter()


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh(refresh_token: str | None = Cookie(default=None)) -> RefreshTokenResponse:
    dto = RefreshDTO(refresh_token=refresh_token or "")
    return refresh_access_token(dto)
