from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.listings import ListingListResponse
from backend.services.listings import list_listings

router = APIRouter(tags=["root"])


@router.get("/")
async def root() -> dict[str, str]:
    return {"detail": "Endpoint is ready"}


@router.get("/listing", response_model=ListingListResponse)
def get_listing(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ListingListResponse:
    return list_listings(db=db, limit=limit, offset=offset, search=search)
