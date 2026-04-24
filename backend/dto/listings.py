from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ListingSortBy = Literal["published_at", "price"]
ListingSortOrder = Literal["asc", "desc"]


class RangeDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: int | float | None = None
    max: int | float | None = None

    @model_validator(mode="after")
    def validate_bounds(self) -> "RangeDTO":
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("Range min cannot be greater than max")
        return self


class ListingSearchDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    property_types: list[str] | None = None
    creator_types: list[Literal["agency", "owner"]] | None = None
    living_conditions: list[str] | None = None
    has_repair: bool | None = None

    price: RangeDTO | None = None
    area: RangeDTO | None = None
    rooms: RangeDTO | None = None
    floor: RangeDTO | None = None
    build_year: RangeDTO | None = None


class ListingDataDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    creator_type: Literal["agency", "owner"] | None = None
    build_year: int | None = None
    has_repair: bool | None = None
    property_type: str | None = None
    living_conditions: list[str] = Field(default_factory=list)
