from __future__ import annotations

import json
import logging
from decimal import Decimal
from json import JSONDecodeError

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.core.listing_cache import ListingListCache
from backend.db.repositories.listings import ListingRepository
from backend.dto.listings import ListingDataDTO, ListingSearchDTO, ListingSortBy, ListingSortOrder
from backend.exceptions import ExternalServiceAppError, ValidationAppError
from backend.logging_utils import log_exception, log_info
from backend.schemas.listings import ListingDataResponse, ListingItemResponse, ListingListResponse

logger = logging.getLogger(__name__)


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
        raise ValidationAppError("Query parameter 'search' must be a valid JSON object") from exc

    if not isinstance(payload, dict):
        raise ValidationAppError("Query parameter 'search' must be a JSON object")

    try:
        return ListingSearchDTO.model_validate(payload)
    except ValidationError as exc:
        raise ValidationAppError(str(exc)) from exc


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
        raise ValidationAppError("Both 'sort_by' and 'sort_order' must be provided together")

    search_dto = _parse_search(search)
    listing_cache = ListingListCache()
    cache_key: str | None = None
    cache_reason: str | None = None

    try:
        cache_key = listing_cache.build_cache_key(
            limit=limit,
            offset=offset,
            search=search_dto,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except Exception:
        log_exception(
            logger, "Failed to build listings cache key", event="listings.cache_key_build_error",
            limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
        )
        cache_key = None
        cache_reason = "cache_key_unavailable"

    if cache_key is not None:
        try:
            cached_response = listing_cache.get_cached_response(cache_key)
        except Exception:
            log_exception(
                logger, "Failed to read listings from cache; falling back to database",
                event="listings.cache_read_error", source="db", reason="cache_read_error",
                limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
            )
            cached_response = None
        if cached_response is not None:
            log_info(
                logger, "Listings served from cache", event="listings.response_served", source="cache",
                limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
            )
            return cached_response
        cache_reason = "cache_unavailable" if not listing_cache._is_available() else "cache_miss"
    elif cache_reason is None:
        cache_reason = "cache_key_unavailable"

    try:
        if cache_reason is None:
            cache_reason = "cache_miss"
        log_info(
            logger, "Listings served from database", event="listings.response_source_selected", source="db",
            reason=cache_reason, limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
        )
        items, total = ListingRepository(db).list_with_filters(
            limit=limit,
            offset=offset,
            search=search_dto,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except SQLAlchemyError as exc:
        log_exception(
            logger, "Database query failed while listing listings", event="listings.db_error",
            source="db", limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
        )
        raise ExternalServiceAppError("Listings service is temporarily unavailable") from exc

    response_items = [
        ListingItemResponse(
            id=item.id,
            aggregator_id=item.aggregator_id,
            external_id=item.external_id,
            url=item.url,
            image_url=item.image_url,
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

    response = ListingListResponse(
        items=response_items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + len(response_items) < total,
    )

    if cache_key is not None:
        try:
            listing_cache.set_cached_response(cache_key, response)
        except Exception:
            log_exception(
                logger, "Failed to write listings response to cache", event="listings.cache_write_error",
                limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
            )

    return response
