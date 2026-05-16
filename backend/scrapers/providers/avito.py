from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import html
import re
from typing import Any
from urllib.parse import urljoin
from urllib.parse import urlparse

import httpx

from backend.core.config import settings
from backend.scrapers.base import ScrapedListingDTO, ScraperParseError, ScraperRequestError


class AvitoScraper:
    aggregator_name = "avito"
    base_url = "https://www.avito.ru"

    def __init__(
        self,
        *,
        search_url: str | None = None,
        timeout_seconds: int | None = None,
        cookie: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        self.search_url = search_url or settings.AVITO_SEARCH_URL
        self.timeout_seconds = timeout_seconds or settings.AVITO_REQUEST_TIMEOUT_SECONDS
        self.cookie = cookie if cookie is not None else settings.AVITO_COOKIE
        self.user_agent = user_agent if user_agent is not None else settings.AVITO_USER_AGENT

    def scrape(self) -> list[ScrapedListingDTO]:
        headers = self._build_headers()
        try:
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
                response = client.get(self.search_url, headers=headers)
        except httpx.HTTPError as exc:
            raise ScraperRequestError(f"Avito request failed: {exc}") from exc

        if response.status_code in {403, 429}:
            raise ScraperRequestError(f"Avito blocked request with status {response.status_code}")
        if response.status_code >= 400:
            raise ScraperRequestError(f"Avito returned status {response.status_code}")
        if self._looks_like_captcha(response.text):
            raise ScraperRequestError("Avito returned captcha page")

        return self.parse(response.text)

    def parse(self, html_text: str) -> list[ScrapedListingDTO]:
        parsed_at = datetime.now(timezone.utc)
        city = _extract_city_from_search_url(self.search_url)
        listings: list[ScrapedListingDTO] = []

        for item_html, external_id in _extract_item_blocks(html_text):
            listing = self._parse_item(
                item_html=item_html,
                external_id=external_id,
                parsed_at=parsed_at,
                city=city,
            )
            if listing is not None:
                listings.append(listing)

        if not listings:
            raise ScraperParseError("Avito page does not contain parseable offers")
        return listings

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ru,ru-RU;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Cookie": self.cookie or "",
            "DNT": "1",
            "Host": "www.avito.ru",
            "Pragma": "no-cache",
            "Priority": "u=0, i",
            "Referer": (
                "https://www.avito.ru/voronezh/kvartiry/sdam/na_dlitelnyy_srok/"
                "ASgBAgECAkSSA8gQ8AeQUgFFxpoMFXsiZnJvbSI6MCwidG8iOjIwMDAwfQ?"
                "context=H4sIAAAAAAAA_wEtANL_YToxOntzOjg6ImZyb21QYWdlIjtzOjE2OiJzZWFyY2hGb3JtV2lkZ2V0Ijt9F_yIfi0AAAA&"
                "f=ASgBAgECBESSA8gQ8AeQUswIkFngwt3NAq7pDwFFxpoMFXsiZnJvbSI6MCwidG8iOjIwMDAwfQ"
            ),
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:150.0) "
                "Gecko/20100101 Firefox/150.0"
            ),
        }
        if self.user_agent:
            headers["User-Agent"] = self.user_agent
        return headers

    def _parse_item(
        self,
        *,
        item_html: str,
        external_id: str,
        parsed_at: datetime,
        city: str | None,
    ) -> ScrapedListingDTO | None:
        title, relative_url = _extract_title_and_url(item_html)
        if title is None or relative_url is None:
            return None

        absolute_url = urljoin(self.base_url, relative_url)
        title_text = _normalize_space(title)
        rooms = _extract_rooms_from_title(title_text)
        area = _extract_area_from_title(title_text)
        floor = _extract_floor_from_title(title_text)

        return ScrapedListingDTO(
            external_id=external_id,
            url=absolute_url,
            image_url=_extract_image_url(item_html),
            published_at=_parse_published_at(_extract_item_date(item_html)),
            parsed_at=parsed_at,
            title=title_text,
            city=city,
            price=_extract_price(item_html),
            rooms=rooms,
            area=area,
            floor=floor,
            data={
                "creator_type": None,
                "build_year": None,
                "has_furniture": None,
                "property_type": "flat",
                "living_conditions": [],
                "source_payload": {
                    "item_id": external_id,
                    "item_date": _extract_item_date(item_html),
                    "item_address": _extract_marker_text(item_html, "item-address"),
                    "item_location": _extract_marker_text(item_html, "item-location"),
                },
            },
        )

    def _looks_like_captcha(self, html_text: str) -> bool:
        lowered = html_text.lower()
        return "captcha" in lowered or "antibot" in lowered


def _extract_item_blocks(html_text: str) -> list[tuple[str, str]]:
    starts = list(
        re.finditer(
            r'<div\s+(?=[^>]*data-marker="item")(?=[^>]*data-item-id="([^"]+)")[^>]*>',
            html_text,
        )
    )
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(starts):
        external_id = match.group(1).strip()
        start = match.start()
        end = starts[index + 1].start() if index + 1 < len(starts) else len(html_text)
        blocks.append((html_text[start:end], external_id))
    return blocks


def _extract_title_and_url(item_html: str) -> tuple[str | None, str | None]:
    match = re.search(
        r'<a\s+(?=[^>]*data-marker="item-title")(?=[^>]*href="([^"]+)")[^>]*>(.*?)</a>',
        item_html,
        flags=re.DOTALL,
    )
    if match is None:
        return None, None
    url = html.unescape(match.group(1))
    title = _strip_tags(match.group(2))
    return title, url


def _extract_image_url(item_html: str) -> str | None:
    match = re.search(
        r'<img\s+(?=[^>]*itemprop="image")(?=[^>]*src="([^"]+)")[^>]*>',
        item_html,
    )
    if match is None:
        return None
    return html.unescape(match.group(1))


def _extract_price(item_html: str) -> float | None:
    meta_match = re.search(
        r'<meta\s+(?=[^>]*itemprop="price")(?=[^>]*content="([^"]+)")[^>]*>',
        item_html,
    )
    if meta_match is not None:
        return _to_float(meta_match.group(1))

    marker_price = _extract_marker_text(item_html, "item-price")
    return _to_float(marker_price)


def _extract_item_date(item_html: str) -> str | None:
    return _extract_marker_text(item_html, "item-date")


def _extract_marker_text(item_html: str, marker: str) -> str | None:
    marker_pattern = re.escape(marker)
    match = re.search(
        rf'<(?P<tag>[a-zA-Z0-9]+)\s+[^>]*data-marker="{marker_pattern}"[^>]*>(?P<body>.*?)</(?P=tag)>',
        item_html,
        flags=re.DOTALL,
    )
    if match is None:
        return None
    return _normalize_space(_strip_tags(match.group("body")))


def _strip_tags(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return html.unescape(without_tags)


def _normalize_space(value: str | None) -> str:
    if value is None:
        return ""
    cleaned = value.replace("\xa0", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = re.sub(r"[^\d,.]", "", value).replace(",", ".")
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _to_int(value: Any) -> int | None:
    numeric = _to_float(value)
    if numeric is None:
        return None
    return int(numeric)


def _extract_rooms_from_title(title: str) -> int | None:
    rooms_match = re.search(r"(\d+)-к\.", title, flags=re.IGNORECASE)
    if rooms_match is not None:
        return _to_int(rooms_match.group(1))
    if "квартира-студия" in title.casefold():
        return 0
    return None


def _extract_area_from_title(title: str) -> float | None:
    area_match = re.search(r"(\d+(?:[.,]\d+)?)\s*м²", title, flags=re.IGNORECASE)
    if area_match is None:
        return None
    return _to_float(area_match.group(1))


def _extract_floor_from_title(title: str) -> int | None:
    floor_match = re.search(r"(\d+)\s*/\s*\d+\s*эт\.", title, flags=re.IGNORECASE)
    if floor_match is None:
        return None
    return _to_int(floor_match.group(1))


def _extract_city_from_search_url(search_url: str) -> str | None:
    path = urlparse(search_url).path
    segments = [segment for segment in path.split("/") if segment]
    if not segments:
        return None
    return segments[0].replace("-", " ").title()


def _parse_published_at(raw_text: str | None) -> datetime | None:
    if raw_text is None:
        return None

    value = _normalize_space(raw_text).casefold()
    if not value:
        return None

    now = datetime.now(timezone.utc)

    minutes_ago_match = re.match(r"^(\d+)\s+мин", value)
    if minutes_ago_match is not None:
        minutes = int(minutes_ago_match.group(1))
        return now - timedelta(minutes=minutes)

    hours_ago_match = re.match(r"^(\d+)\s+час", value)
    if hours_ago_match is not None:
        hours = int(hours_ago_match.group(1))
        return now - timedelta(hours=hours)

    today_time_match = re.match(r"^сегодня\s+(\d{1,2}):(\d{2})$", value)
    if today_time_match is not None:
        hour = int(today_time_match.group(1))
        minute = int(today_time_match.group(2))
        return datetime.combine(now.date(), time(hour=hour, minute=minute), tzinfo=timezone.utc)

    yesterday_time_match = re.match(r"^вчера\s+(\d{1,2}):(\d{2})$", value)
    if yesterday_time_match is not None:
        hour = int(yesterday_time_match.group(1))
        minute = int(yesterday_time_match.group(2))
        return datetime.combine(
            now.date() - timedelta(days=1),
            time(hour=hour, minute=minute),
            tzinfo=timezone.utc,
        )

    absolute_match = re.match(
        r"^(\d{1,2})\s+([а-яё]+)(?:\s+(\d{4}))?(?:\s+(\d{1,2}):(\d{2}))?$",
        value,
    )
    if absolute_match is None:
        return None

    day = int(absolute_match.group(1))
    month_value = _RUSSIAN_MONTHS.get(absolute_match.group(2))
    if month_value is None:
        return None

    year = int(absolute_match.group(3)) if absolute_match.group(3) else now.year
    hour = int(absolute_match.group(4)) if absolute_match.group(4) else 0
    minute = int(absolute_match.group(5)) if absolute_match.group(5) else 0

    try:
        parsed_date = date(year=year, month=month_value, day=day)
    except ValueError:
        return None

    return datetime.combine(parsed_date, time(hour=hour, minute=minute), tzinfo=timezone.utc)


_RUSSIAN_MONTHS: dict[str, int] = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}
