from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ListingDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    creator_type: str | None = None
    build_year: int | None = None
    has_repair: bool | None = None
    property_type: str | None = None
    living_conditions: list[str] = Field(default_factory=list)


class ListingItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    aggregator_id: int
    external_id: str
    url: str
    published_at: datetime | None
    parsed_at: datetime | None
    title: str
    price: float | None
    rooms: int | None
    area: float | None
    floor: int | None
    data: ListingDataResponse


class ListingListResponse(BaseModel):
    items: list[ListingItemResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
