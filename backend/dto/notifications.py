from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from backend.dto.listings import RangeDTO


class NotificationSettingsDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city: str
    notify_email: bool
    notify_push: bool
    property_types: list[str] | None = None
    creator_types: list[str] | None = None
    living_conditions: list[str] | None = None
    has_repair: bool | None = None
    price: RangeDTO | None = None
    area: RangeDTO | None = None
    rooms: RangeDTO | None = None
    floor: RangeDTO | None = None
    build_year: RangeDTO | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("creator_types", mode="before")
    @classmethod
    def normalize_creator_types(cls, value):
        if value is None:
            return None
        if not isinstance(value, list):
            raise ValueError("creator_types must be a list")
        cleaned = [str(item).strip().lower() for item in value if str(item).strip()]
        if not cleaned:
            return None
        if all(item == "string" for item in cleaned):
            return None
        allowed = {"agency", "owner"}
        invalid = [item for item in cleaned if item not in allowed]
        if invalid:
            raise ValueError("creator_types must contain only 'agency' or 'owner'")
        return cleaned

    @model_validator(mode="after")
    def validate_channels(self) -> "NotificationSettingsDTO":
        if not self.notify_email and not self.notify_push:
            raise ValueError("At least one channel must be enabled")
        return self


class PushSubscriptionDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    endpoint: str
    p256dh: str
    auth: str
    user_agent: str | None = None
