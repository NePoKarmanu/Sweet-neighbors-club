from __future__ import annotations

import json
from decimal import Decimal
from json import JSONDecodeError

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.db.repositories.listings import ListingRepository
from backend.dto.listings import ListingDataDTO, ListingSearchDTO, ListingSortBy, ListingSortOrder
from backend.schemas.listings import ListingDataResponse, ListingItemResponse, ListingListResponse


def _to_float(value: Decimal | float | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


def _parse_search(search: str | None) -> ListingSearchDTO:
    if search is None:
        return ListingSearchDTO()

    try:
        payload = json.loads(search)
    except JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query parameter 'search' must be a valid JSON object",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query parameter 'search' must be a JSON object",
        )

    try:
        return ListingSearchDTO.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc


def _normalize_listing_data(raw_data: dict | None) -> ListingDataResponse:
    data = raw_data if isinstance(raw_data, dict) else {}
    try:
        normalized = ListingDataDTO.model_validate(data)
    except ValidationError:
        normalized = ListingDataDTO()
    return ListingDataResponse.model_validate(normalized)


def list_listings(
    *,
    db: Session,
    limit: int,
    offset: int,
    search: str | None,
    sort_by: ListingSortBy | None,
    sort_order: ListingSortOrder | None,
) -> ListingListResponse:
    if (sort_by is None) != (sort_order is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Both 'sort_by' and 'sort_order' must be provided together",
        )

    search_dto = _parse_search(search)
    items, total = ListingRepository(db).list_with_filters(
        limit=limit,
        offset=offset,
        search=search_dto,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    response_items = [
        ListingItemResponse(
            id=item.id,
            aggregator_id=item.aggregator_id,
            external_id=item.external_id,
            url=item.url,
            published_at=item.published_at,
            parsed_at=item.parsed_at,
            title=item.title,
            price=_to_float(item.price),
            rooms=item.rooms,
            area=_to_float(item.area),
            floor=item.floor,
            data=_normalize_listing_data(item.data),
        )
        for item in items
    ]

    return ListingListResponse(
        items=response_items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + len(response_items) < total,
    )
