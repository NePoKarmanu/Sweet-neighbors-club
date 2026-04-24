from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.dto.listings import ListingSortBy, ListingSortOrder
from backend.schemas.listings import ListingListResponse
from backend.services.listings import list_listings

router = APIRouter(tags=["listing"])


@router.get("/listing", response_model=ListingListResponse)
def get_listing(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
    sort_by: ListingSortBy | None = Query(default=None),
    sort_order: ListingSortOrder | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ListingListResponse:
    return list_listings(
        db=db,
        limit=limit,
        offset=offset,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
