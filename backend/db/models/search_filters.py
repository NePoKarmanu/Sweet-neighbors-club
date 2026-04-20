from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class SearchFilter(Base):
    __tablename__ = "search_filters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), nullable=False)

    city: Mapped[str] = mapped_column(String(128), nullable=False)
    price_min: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    price_max: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    rooms_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rooms_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_min: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    area_max: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    floor_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    floor_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    additional_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    subscription: Mapped["Subscription"] = relationship(back_populates="search_filters")
