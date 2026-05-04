from fastapi import APIRouter

from backend.dto.auth import RefreshDTO
from backend.schemas.auth import RefreshRequest, RefreshTokenResponse
from backend.services.signin import refresh_access_token

router = APIRouter()


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh(payload: RefreshRequest) -> RefreshTokenResponse:
    dto = RefreshDTO(refresh_token=payload.refresh_token)
    return refresh_access_token(dto)
