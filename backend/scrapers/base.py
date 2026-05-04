from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


class ScraperRequestError(Exception):
    pass


class ScraperParseError(Exception):
    pass


class ScraperProviderNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class ScrapedListingDTO:
    external_id: str
    url: str
    title: str
    city: str | None = None
    published_at: datetime | None = None
    parsed_at: datetime | None = None
    price: float | None = None
    rooms: int | None = None
    area: float | None = None
    floor: int | None = None
    data: dict = field(default_factory=dict)

    def to_repository_payload(self) -> dict:
        return {
            "external_id": self.external_id,
            "url": self.url,
            "published_at": self.published_at,
            "parsed_at": self.parsed_at,
            "title": self.title,
            "city": self.city,
            "price": self.price,
            "rooms": self.rooms,
            "area": self.area,
            "floor": self.floor,
            "data": self.data,
        }


class ListingScraper(Protocol):
    aggregator_name: str
    base_url: str

    def scrape(self) -> list[ScrapedListingDTO]:
        ...
