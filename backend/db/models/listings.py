from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint("aggregator_id", "external_id", name="uq_listings_aggregator_external_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    aggregator_id: Mapped[int] = mapped_column(ForeignKey("aggregators.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)

    url: Mapped[str] = mapped_column(String(1024), nullable=False)

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    rooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    floor: Mapped[int | None] = mapped_column(Integer, nullable=True)

    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    aggregator: Mapped["Aggregator"] = relationship(back_populates="listings")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="listing")
    sent_listings: Mapped[list["SentListing"]] = relationship(back_populates="listing")
