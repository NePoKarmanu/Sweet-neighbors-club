from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from backend.dto.listings import RangeDTO


class NotificationSettingsRequest(BaseModel):
    city: str = Field(min_length=1, max_length=128)
    notify_email: bool = True
    notify_push: bool = True
    property_types: list[str] | None = None
    creator_types: list[str] | None = Field(
        default=None,
        description="Allowed values: agency, owner. Omit this field to match all creator types.",
        examples=[["agency"], ["owner"], ["agency", "owner"]],
    )
    living_conditions: list[str] | None = None
    has_repair: bool | None = None
    price: RangeDTO | None = None
    area: RangeDTO | None = None
    rooms: RangeDTO | None = None
    floor: RangeDTO | None = None
    build_year: RangeDTO | None = None
    start_date: date | None = None
    end_date: date | None = None


class NotificationSettingsResponse(BaseModel):
    subscription_id: int
    filter_id: int
    notify_email: bool
    notify_push: bool
    is_active: bool


class PushSubscriptionRequest(BaseModel):
    endpoint: str = Field(min_length=1, max_length=1024)
    p256dh: str = Field(min_length=1, max_length=512)
    auth: str = Field(min_length=1, max_length=512)
    user_agent: str | None = Field(default=None, max_length=512)


class PushSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    endpoint: str
    is_active: bool


class NotificationPipelineRunResponse(BaseModel):
    task_id: str
    mode: str
    user_id: int | None = None


class NotificationPipelineTaskResult(BaseModel):
    created_notifications: int
    created_deliveries: int
    processed_deliveries: int
    user_id: int | None = None


class NotificationPipelineTaskStatusResponse(BaseModel):
    task_id: str
    state: str
    result: NotificationPipelineTaskResult | None
