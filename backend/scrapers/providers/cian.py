from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from html import unescape
from typing import Any
from urllib.parse import urljoin

import httpx

from backend.core.config import settings
from backend.scrapers.base import ScrapedListingDTO, ScraperParseError, ScraperRequestError


class CianScraper:
    aggregator_name = "cian"
    base_url = "https://voronezh.cian.ru"

    def __init__(
        self,
        *,
        search_url: str | None = None,
        timeout_seconds: int | None = None,
        cookie: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        self.search_url = search_url or settings.CIAN_SEARCH_URL
        self.timeout_seconds = timeout_seconds or settings.CIAN_REQUEST_TIMEOUT_SECONDS
        self.cookie = cookie if cookie is not None else settings.CIAN_COOKIE
        self.user_agent = user_agent if user_agent is not None else settings.CIAN_USER_AGENT

    def scrape(self) -> list[ScrapedListingDTO]:
        headers = self._build_headers()
        try:
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
                response = client.get(self.search_url, headers=headers)
        except httpx.HTTPError as exc:
            raise ScraperRequestError(f"Cian request failed: {exc}") from exc

        if response.status_code in {403, 429}:
            raise ScraperRequestError(f"Cian blocked request with status {response.status_code}")
        if response.status_code >= 400:
            raise ScraperRequestError(f"Cian returned status {response.status_code}")
        if self._looks_like_captcha(response.text):
            raise ScraperRequestError("Cian returned captcha page")

        return self.parse(response.text)

    def parse(self, html: str) -> list[ScrapedListingDTO]:
        config = _extract_frontend_serp_config(html)
        state = config.get("defaultState", config)
        offers = _find_offer_list(state)
        parsed_at = datetime.now(timezone.utc)

        listings = [
            listing
            for offer in offers
            if (listing := self._parse_offer(offer, parsed_at=parsed_at)) is not None
        ]
        if not listings:
            raise ScraperParseError("Cian state does not contain parseable offers")
        return listings

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ru,ru-RU;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Cookie": (
                "_CIAN_GK=04b7036c-306f-4828-b763-8f83bb6d1f46; _yasc=DbEu4Air5MWnalea99BaF2OT12RFgLmbaow0G3IQTXOaO1OcvyCgXOzI/i6FNB3NCW4=; _yasc=pZEgyt4MZtOtlsEr2UJjZroQnqYA55CiGVoOgmPpzB5l5ZHePPYQ9rHb94743S43ToMlCA==; cookie_agreement_accepted=1; frontend-offer-card.consultant_chat_onboarding_shown=1; forever_region_id=4713; forever_region_name=%D0%92%D0%BE%D1%80%D0%BE%D0%BD%D0%B5%D0%B6; frontend-serp.offer_chat_onboarding_shown=1; frontend-serp.chatAnimationShownCount=1; frontend-serp.chatAnimationCounter=3; frontend-offer-card.newbuilding_broker_onboarding_shown=1; newbuilding_mortgage_payment_filter_onboarding=1; session_region_id=4713; do_not_show_mortgage_banner=1; frontend-offer-card.newbuilding_broker_onboarding_shown=1; newbuilding_mortgage_payment_filter_onboarding=1; session_region_name=%D0%92%D0%BE%D1%80%D0%BE%D0%BD%D0%B5%D0%B6; sopr_session=b50e61de0b5f4773; session_main_town_region_id=4713"
            ),
            "DNT": "1",
            "Host": "voronezh.cian.ru",
            "Pragma": "no-cache",
            "Priority": "u=0, i=0",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Sec-GPC": "1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:150.0) "
                "Gecko/20100101 Firefox/150.0"
            ),
        }
        if self.cookie:
            headers["Cookie"] = self.cookie
        if self.user_agent:
            headers["User-Agent"] = self.user_agent
        return headers

    def _parse_offer(
        self,
        offer: dict[str, Any],
        *,
        parsed_at: datetime,
    ) -> ScrapedListingDTO | None:
        external_id = _to_string(_first_deep_value(offer, ("id", "cianId", "offerId")))
        url = _to_string(_first_deep_value(offer, ("url", "canonicalUrl", "fullUrl")))
        if external_id is None:
            return None

        if url is None:
            url = f"/rent/flat/{external_id}/"

        absolute_url = urljoin(self.base_url, url)
        title = _to_string(_first_deep_value(offer, ("title", "subtitle", "header")))
        return ScrapedListingDTO(
            external_id=external_id,
            url=absolute_url,
            published_at=_to_datetime(
                _first_deep_value(offer, ("publishedAt", "creationDate", "addedTimestamp"))
            ),
            parsed_at=parsed_at,
            title=title or f"Cian listing {external_id}",
            price=_to_float(_first_deep_value(offer, ("price", "priceRur", "totalPrice"))),
            rooms=_to_int(_first_deep_value(offer, ("rooms", "roomsCount", "roomCount"))),
            area=_to_float(_first_deep_value(offer, ("totalArea", "area", "allArea"))),
            floor=_to_int(_first_deep_value(offer, ("floor", "floorNumber"))),
            data={
                "creator_type": _normalize_creator_type(
                    _first_deep_value(offer, ("creator_type", "creatorType", "sellerType", "userType"))
                ),
                "build_year": _to_int(_first_deep_value(offer, ("buildYear", "build_year"))),
                "has_repair": _to_bool(_first_deep_value(offer, ("hasRepair", "has_repair", "repair"))),
                "property_type": _to_string(
                    _first_deep_value(offer, ("propertyType", "property_type", "offerType"))
                ),
                "living_conditions": _to_string_list(
                    _first_deep_value(offer, ("livingConditions", "living_conditions"))
                ),
                "source_payload": offer,
            },
        )

    def _looks_like_captcha(self, html: str) -> bool:
        lowered = html.lower()
        return "captcha" in lowered or "captcha-container" in lowered


def _extract_frontend_serp_config(html: str) -> dict[str, Any]:
    for marker in (
        "window._cianConfig['frontend-serp']",
        'window._cianConfig["frontend-serp"]',
    ):
        marker_index = html.find(marker)
        if marker_index == -1:
            continue
        assignment_index = html.find("=", marker_index)
        if assignment_index == -1:
            continue

        # New Cian format:
        # window._cianConfig['frontend-serp'] =
        #   (window._cianConfig['frontend-serp'] || []).concat([{key, value}, ...]);
        concat_index = html.find(".concat([", assignment_index)
        if concat_index != -1:
            list_start = html.find("[", concat_index)
            if list_start != -1:
                raw_list = _read_balanced_list(html, list_start)
                decoded_list = _loads_json(raw_list)
                if isinstance(decoded_list, list):
                    mapped = _map_config_entries(decoded_list)
                    if mapped:
                        return mapped

        # Legacy format where frontend-serp is assigned directly to object.
        object_start = html.find("{", assignment_index)
        if object_start != -1:
            raw_object = _read_balanced_object(html, object_start)
            decoded = _loads_json(raw_object)
            if isinstance(decoded, dict):
                return decoded

    raise ScraperParseError("Cian frontend-serp config was not found")


def _read_balanced_object(text: str, start_index: int) -> str:
    depth = 0
    in_string = False
    escaped = False
    quote = ""

    for index in range(start_index, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                in_string = False
            continue

        if char in {'"', "'"}:
            in_string = True
            quote = char
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start_index : index + 1]

    raise ScraperParseError("Cian frontend-serp config is incomplete")


def _read_balanced_list(text: str, start_index: int) -> str:
    depth = 0
    in_string = False
    escaped = False
    quote = ""

    for index in range(start_index, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                in_string = False
            continue

        if char in {'"', "'"}:
            in_string = True
            quote = char
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return text[start_index : index + 1]

    raise ScraperParseError("Cian frontend-serp config list is incomplete")


def _loads_json(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        try:
            return json.loads(unescape(raw))
        except json.JSONDecodeError:
            raise ScraperParseError("Cannot decode Cian frontend-serp config") from exc


def _map_config_entries(entries: list[Any]) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        key = entry.get("key")
        if not isinstance(key, str):
            continue
        mapped[key] = entry.get("value")
    return mapped


def _find_offer_list(state: Any) -> list[dict[str, Any]]:
    if isinstance(state, dict):
        direct_products = state.get("products")
        if isinstance(direct_products, list):
            direct_product_offers = [item for item in direct_products if isinstance(item, dict)]
            if direct_product_offers:
                return direct_product_offers

    best: list[dict[str, Any]] = []
    best_score = 0

    def visit(value: Any) -> None:
        nonlocal best, best_score
        if isinstance(value, list):
            offers = [item for item in value if isinstance(item, dict)]
            score = sum(1 for item in offers if _looks_like_offer(item))
            if score > best_score:
                best = offers
                best_score = score
            for item in value:
                visit(item)
            return

        if isinstance(value, dict):
            for child in value.values():
                visit(child)

    visit(state)
    if best_score == 0:
        raise ScraperParseError("Cian offers list was not found")
    return best


def _looks_like_offer(value: dict[str, Any]) -> bool:
    has_id = _first_deep_value(value, ("id", "cianId", "offerId")) is not None
    has_url = _first_deep_value(value, ("url", "canonicalUrl", "fullUrl")) is not None
    has_listing_data = _first_deep_value(value, ("price", "title", "totalArea", "roomsCount")) is not None
    has_product_shape = _first_deep_value(value, ("position", "photosCount", "dealType")) is not None
    return has_id and ((has_url and has_listing_data) or (has_product_shape and has_listing_data))


def _first_deep_value(value: Any, keys: tuple[str, ...]) -> Any:
    if isinstance(value, dict):
        for key in keys:
            if key in value and value[key] is not None:
                return value[key]
        for child in value.values():
            found = _first_deep_value(child, keys)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _first_deep_value(child, keys)
            if found is not None:
                return found
    return None


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
    if isinstance(value, dict):
        value = _first_deep_value(value, ("value", "amount", "price", "rur"))
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
    number = _to_float(value)
    if number is None:
        return None
    return int(number)


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return None


def _to_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 10_000_000_000:
            timestamp = timestamp / 1000
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _normalize_creator_type(value: Any) -> str | None:
    text = _to_string(value)
    if text is None:
        return None
    lowered = text.lower()
    if lowered in {"owner", "private", "person"}:
        return "owner"
    if lowered in {"agency", "agent", "realtor", "developer"}:
        return "agency"
    return None


def _to_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in (_to_string(item) for item in value) if item is not None]
    text = _to_string(value)
    if text is None:
        return []
    return [text]
