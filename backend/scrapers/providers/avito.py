from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import html
import json
import re
from typing import Any
from urllib.parse import urljoin
from urllib.parse import urlparse

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

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
        timeout_ms = int(self.timeout_seconds * 1000)
        try:
            with sync_playwright() as playwright:
                browser = playwright.firefox.launch(headless=True)
                context = browser.new_context(user_agent=headers["User-Agent"])
                if self.cookie:
                    context.add_cookies(_parse_cookies_header(self.cookie, self.search_url))
                page = context.new_page()
                page.goto(self.search_url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.wait_for_selector('[data-marker="item"]', timeout=timeout_ms)
                html_text = page.content()
                context.close()
                browser.close()
        except (PlaywrightTimeoutError, PlaywrightError) as exc:
            raise ScraperRequestError(f"Avito request failed: {exc}") from exc

        #if self._looks_like_captcha(html_text):
            #raise ScraperRequestError("Avito returned captcha page")

        return self.parse(html_text)

    def parse(self, html_text: str) -> list[ScrapedListingDTO]:
        parsed_at = datetime.now(timezone.utc)
        city = _extract_city_from_search_url(self.search_url)
        raw_payload_by_id = _extract_raw_payload_by_external_id(html_text)
        listings: list[ScrapedListingDTO] = []

        for item_html, external_id in _extract_item_blocks(html_text):
            listing = self._parse_item(
                item_html=item_html,
                external_id=external_id,
                parsed_at=parsed_at,
                city=city,
                raw_payload=raw_payload_by_id.get(external_id),
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
            "Cookie": "sx; sx; cookie_consent_shown=1; sx; SEARCH_HISTORY_IDS=1%2C4%2C; selected_locale=ru-RU; buyer_from_page=catalog; srv_id=p_yxx5WIWhi8XIk6.r3GW6i8iB7pu_60Y9Pip2TRN-WFmrX_xHv6JGxY-GqB5NsdyJRJoxA9SEQ9F39zUARTo.idceF8MtDLMboZWO_8DS-IJw5EOVkgXg9yzCh9eDTmc=.web; _adcc=2.MQ/VecSAW2Tc5KdDv92bG+CJkakA6dzjZ9fIMgosZLGkwPUxiR1TRi51si4uiOZ4cmUWyvWdM36nszBcdfEriHNRQ0KosMIqULjHA/URMxOB9TLykvlNmwIq7BxzhYEYyK9IZ2EwFXB5OonxmjDalsmITbO/; u=3bok4jtk.1gf1vj9.1l5zqrvhwsk0; v=1779440920; cssid=5a78270c-63b7-4183-8f17-e30769f3e196; buyer_location_id=625810; csprefid=64d48552-c7a8-444e-9af8-1d1a78d0b1a1; cssid_exp=1779442723754; luri=voronezh; sx=H4sIAAAAAAAC/6pWMjFMTEk2SEu1SLRIMTa2NDFKs0xNMzczMUkztTQzNktRsqpWKlOyUvINSHXMMI1KCjcLLPdPySlR0lFKVbIyNDe3NDUytzQ3ra0FBAAA//8jLi28TAAAAA==; f=5.0c4f4b6d233fb90636b4dd61b04726f147e1eada7172e06c47e1eada7172e06c47e1eada7172e06c47e1eada7172e06cb59320d6eb6303c1b59320d6eb6303c1b59320d6eb6303c147e1eada7172e06c8a38e2c5b3e08b898a38e2c5b3e08b890df103df0c26013a7b0d53c7afc06d0b2ebf3cb6fd35a0ac7b0d53c7afc06d0b0df103df0c26013ae2bfa4611aac769efa4d7ea84258c63d74c4a16376f87ccd164b09365f5308e7f12b79bbb67ac37d34d62295fceb188d46b8ae4e81acb9fa46b8ae4e81acb9fa46b8ae4e81acb9fa46b8ae4e81acb9fa46b8ae4e81acb9fa46b8ae4e81acb9fa46b8ae4e81acb9fa46b8ae4e81acb9fa46b8ae4e81acb9fa46b8ae4e81acb9faf5b2e7701475d0f8352c31daf983fa077a7b6c33f74d335cfa601f10c363b543953cc22f15e8abc602c730c0109b9fbbc356e17b0dce01ea90e8aac858442de29154f4aaf0a7b4f48f10b78f884930fa48ded966eb8e3c6e46b8ae4e81acb9fa46b8ae4e81acb9fa02c68186b443a7ac4fb676a7b5ee221228bf1e74f86dc6052da10fb74cac1eab2da10fb74cac1eabc7bcb3d5c63c9a582f4a9c22eedccd9675dded44b42a0d02; gMltIuegZN2COuSe=EOFGWsm50bhh17prLqaIgdir1V0kgrvN; ft=%229BZlh0PQfvq1AiiUgYWnXCzodwfLD7UHYcSm2xEV1jkghToGN20LtREysA+HDJNojyYl1+cE6r5xEOJHGUdOyHGLc2I/Ky9gQcl1myy21UBp+4+UdpxyUcUkFP57/LabZi6vrzPg/7wNhM7wnMEy0Q==%22",
            "DNT": "1",
            "Host": "www.avito.ru",
            "Pragma": "no-cache",
            "Priority": "u=0, i",
            "Referer": (
                "https://www.avito.ru/voronezh/kvartiry/sdam/na_dlitelnyy_srok"
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
        raw_payload: dict[str, Any] | None,
    ) -> ScrapedListingDTO | None:
        title, relative_url = _extract_title_and_url(item_html)
        if title is None or relative_url is None:
            return None

        title_text = _normalize_space(title)
        absolute_url = urljoin(self.base_url, relative_url)
        image_url = _extract_image_url(item_html, raw_payload=raw_payload)
        raw_date = _extract_item_date(item_html, raw_payload=raw_payload)

        return ScrapedListingDTO(
            external_id=external_id,
            url=absolute_url,
            image_url=image_url,
            published_at=_parse_published_at(raw_date),
            parsed_at=parsed_at,
            title=title_text,
            city=city,
            price=_extract_price(item_html, raw_payload=raw_payload),
            rooms=_extract_rooms_from_title(title_text),
            area=_extract_area_from_title(title_text),
            floor=_extract_floor_from_title(title_text),
            data={
                "creator_type": None,
                "build_year": None,
                "has_furniture": None,
                "property_type": "flat",
                "living_conditions": [],
                "source_payload": raw_payload if raw_payload is not None else {},
            },
        )

    def _looks_like_captcha(self, html_text: str) -> bool:
        lowered = html_text.lower()
        return "captcha" in lowered or "antibot" in lowered


def _extract_raw_payload_by_external_id(html_text: str) -> dict[str, dict[str, Any]]:
    state = _extract_mfe_state(html_text)
    payload_by_id: dict[str, tuple[int, dict[str, Any]]] = {}
    stack: list[Any] = [state]

    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            score = _raw_item_score(node)
            if score > 0:
                external_id = _to_string(node.get("id"))
                if external_id is not None:
                    current = payload_by_id.get(external_id)
                    if current is None or score > current[0]:
                        payload_by_id[external_id] = (score, node)
            for value in node.values():
                stack.append(value)
            continue
        if isinstance(node, list):
            for item in node:
                stack.append(item)

    return {external_id: payload for external_id, (_, payload) in payload_by_id.items()}


def _parse_cookies_header(cookie_header: str, url: str) -> list[dict[str, str]]:
    domain = urlparse(url).hostname or "www.avito.ru"
    cookies: list[dict[str, str]] = []
    for raw_part in cookie_header.split(";"):
        part = raw_part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        name = name.strip()
        if not name:
            continue
        cookies.append(
            {
                "name": name,
                "value": value.strip(),
                "domain": domain,
                "path": "/",
            }
        )
    return cookies


def _extract_mfe_state(html_text: str) -> dict[str, Any]:
    scripts = re.findall(
        r'<script[^>]*data-mfe-state="true"[^>]*>(.*?)</script>',
        html_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not scripts:
        return {}

    for script_content in scripts:
        decoded = html.unescape(script_content)
        try:
            payload = json.loads(decoded)
        except json.JSONDecodeError:
            continue
        if (
            isinstance(payload, dict)
            and isinstance(payload.get("state"), dict)
            and isinstance(payload["state"].get("data"), dict)
        ):
            return payload["state"]
    return {}


def _raw_item_score(value: dict[str, Any]) -> int:
    has_id = _to_string(value.get("id")) is not None
    if not has_id:
        return 0

    keys = (
        "title",
        "urlPath",
        "priceDetailed",
        "images",
        "location",
        "description",
        "iva",
    )
    score = sum(1 for key in keys if key in value and value.get(key) is not None)
    return score if score >= 3 else 0


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
    return _strip_tags(match.group(2)), html.unescape(match.group(1))


def _extract_image_url(item_html: str, *, raw_payload: dict[str, Any] | None) -> str | None:
    if raw_payload is not None:
        images = raw_payload.get("images")
        if isinstance(images, list) and images and isinstance(images[0], dict):
            image_url = _to_string(images[0].get("url"))
            if image_url is not None:
                return image_url

    match = re.search(
        r'<img\s+(?=[^>]*item[pP]rop="image")(?=[^>]*src="([^"]+)")[^>]*>',
        item_html,
    )
    if match is not None:
        return html.unescape(match.group(1))
    return _extract_slider_image_url(item_html)


def _extract_slider_image_url(item_html: str) -> str | None:
    slider_match = re.search(
        r'data-marker="slider-image/image-(https://[^"]+)"',
        item_html,
    )
    if slider_match is None:
        return None
    return html.unescape(slider_match.group(1))


def _extract_meta_price(item_html: str) -> str | None:
    meta_match = re.search(
        r'<meta\s+(?=[^>]*item[pP]rop="price")(?=[^>]*content="([^"]+)")[^>]*>',
        item_html,
    )
    if meta_match is None:
        return None
    return html.unescape(meta_match.group(1))


def _extract_price(item_html: str, *, raw_payload: dict[str, Any] | None) -> float | None:
    if raw_payload is not None:
        price_detailed = raw_payload.get("priceDetailed")
        if isinstance(price_detailed, dict):
            value = _to_float(price_detailed.get("value"))
            if value is not None:
                return value
        normalized_price = _to_float(raw_payload.get("normalizedPrice"))
        if normalized_price is not None:
            return normalized_price

    meta_price = _extract_meta_price(item_html)
    if meta_price is not None:
        return _to_float(meta_price)

    marker_price = _extract_marker_text(item_html, "item-price")
    return _to_float(marker_price)


def _extract_item_date(item_html: str, *, raw_payload: dict[str, Any] | None) -> str | None:
    if raw_payload is not None:
        iva = raw_payload.get("iva")
        if isinstance(iva, dict):
            date_info_step = iva.get("DateInfoStep")
            if isinstance(date_info_step, list) and date_info_step:
                first = date_info_step[0]
                if isinstance(first, dict):
                    payload = first.get("payload")
                    if isinstance(payload, dict):
                        relative = _to_string(payload.get("relative"))
                        if relative is not None:
                            return relative
                        absolute = _to_string(payload.get("absolute"))
                        if absolute is not None:
                            return absolute
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


def _to_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if isinstance(value, (int, float)):
        return str(value)
    return None


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
        return now - timedelta(minutes=int(minutes_ago_match.group(1)))

    hours_ago_match = re.match(r"^(\d+)\s+час", value)
    if hours_ago_match is not None:
        return now - timedelta(hours=int(hours_ago_match.group(1)))

    today_time_match = re.match(r"^сегодня\s+(\d{1,2}):(\d{2})$", value)
    if today_time_match is not None:
        return datetime.combine(
            now.date(),
            time(hour=int(today_time_match.group(1)), minute=int(today_time_match.group(2))),
            tzinfo=timezone.utc,
        )

    yesterday_time_match = re.match(r"^вчера\s+(\d{1,2}):(\d{2})$", value)
    if yesterday_time_match is not None:
        return datetime.combine(
            now.date() - timedelta(days=1),
            time(hour=int(yesterday_time_match.group(1)), minute=int(yesterday_time_match.group(2))),
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
