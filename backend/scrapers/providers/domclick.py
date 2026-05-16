from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from backend.core.config import settings
from backend.scrapers.base import ScrapedListingDTO, ScraperParseError, ScraperRequestError


class DomclickScraper:
    aggregator_name = "domclick"
    base_url = "https://voronezh.domclick.ru"

    def __init__(
        self,
        *,
        search_url: str | None = None,
        timeout_seconds: int | None = None,
        cookie: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        self.search_url = search_url or settings.DOMCLICK_SEARCH_URL
        self.timeout_seconds = timeout_seconds or settings.DOMCLICK_REQUEST_TIMEOUT_SECONDS
        self.cookie = cookie if cookie is not None else settings.DOMCLICK_COOKIE
        self.user_agent = user_agent if user_agent is not None else settings.DOMCLICK_USER_AGENT

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ru,ru-RU;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Cookie": "region={%22data%22:{%22name%22:%22%D0%92%D0%BE%D1%80%D0%BE%D0%BD%D0%B5%D0%B6%22%2C%22regionGuid%22:%2270725a3f-da87-4116-a9ca-7bf45cefdfea%22%2C%22localityGuid%22:%22a7b6f76c-4fa7-41b6-9351-0f3ec1eb4ac1%22%2C%22subdomain%22:%22voronezh%22}%2C%22isAutoResolved%22:true}; canary-bind-id-13626=next-1; qrator_jsid2=v2.0.1778935447.415.bceb14e5R6Q0decP|6e4lo5lEVCxDAq81|K9588EAm8cDT98MGfPt1NPtNXT38kjTlaN0+9HMkJvKUCxMs9WTYxZQM6Dclwah3wFYyAiXYOwlnaYRRCP4ElcMIFSsqU/WbmurGvtnLXCm4H+wSHJPIRgNFoSbd5/+T97pdjahzMrWq/xMR5etl58Qx072D+QbOmw5k5j5ryns=-rFMZcFVog5SctNectNd+9JekSgc=; _sa=SA1.6f8409bc-0e62-4988-98e6-e31562e95d64.1778935452; autoDefinedRegion=a7b6f76c-4fa7-41b6-9351-0f3ec1eb4ac1:70725a3f-da87-4116-a9ca-7bf45cefdfea:%D0%92%D0%BE%D1%80%D0%BE%D0%BD%D0%B5%D0%B6:voronezh; currentLocalityGuid=a7b6f76c-4fa7-41b6-9351-0f3ec1eb4ac1; currentRegionGuid=70725a3f-da87-4116-a9ca-7bf45cefdfea; currentSubDomain=voronezh; dddIntroOnline=false; iosAppLink=; logoSuffix=; max-chat-settings-show={%22countOfEntry%22:4,%22lastStatus%22:%22NOT_CREATED%22}; ns_session=151ee6ce-d769-4eda-9bfe-cabbc78700c4; regionAlert=1; regionName=a7b6f76c-4fa7-41b6-9351-0f3ec1eb4ac1:%D0%92%D0%BE%D1%80%D0%BE%D0%BD%D0%B5%D0%B6; showDddIntro=false; RETENTION_COOKIES_NAME=ff13b0d735334ee981156ee103428002:9Higo4sMiRk7Z2ShkE3m7lZdFCg; sessionId=05332905c4a6479e90966776111aed93:OvAh8elxGanPglpgmD2t5zFSwuY; UNIQ_SESSION_ID=01f080e1df004abeab8095e7beb83cfc:mduPhVQcAsKm2vSlcyty8tx8rN8; _visitId=eed692ab-8539-47dc-9509-c25a42e1bfd2-8cd1520ebd0d580d; _sas.2c534172f17069dd8844643bb4eb639294cd4a7a61de799648e70dc86bc442b9=SA1.6f8409bc-0e62-4988-98e6-e31562e95d64.1778935452.1778946103; _sas=SA1.6f8409bc-0e62-4988-98e6-e31562e95d64.1778935452.1778946103; project-3518=1318232-1",
            "DNT": "1",
            "Host": "voronezh.domclick.ru",
            "Pragma": "no-cache",
            "Priority": "u=0, i",
            "Referer": "https://voronezh.domclick.ru/search?deal_type=rent&category=living&offer_type=flat&offset=0",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
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

    def scrape(self) -> list[ScrapedListingDTO]:
        try:
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
                response = client.get(self.search_url, headers=self._build_headers())
        except httpx.HTTPError as exc:
            raise ScraperRequestError(f"Domclick request failed: {exc}") from exc

        if response.status_code in {401, 403, 429}:
            raise ScraperRequestError(
                f"Domclick blocked request with status {response.status_code}"
            )
        if response.status_code >= 400:
            raise ScraperRequestError(f"Domclick returned status {response.status_code}")
        lowered = response.text.lower()
        if "qrator" in lowered or "captcha" in lowered:
            raise ScraperRequestError("Domclick returned antibot/captcha page")

        return self.parse(response.text)

    def parse(self, html: str) -> list[ScrapedListingDTO]:
        state = _extract_ssr_state(html)
        search = state.get("search") if isinstance(state, dict) else None
        pages = search.get("pages") if isinstance(search, dict) else None
        first_page = pages.get("0") if isinstance(pages, dict) else None
        ids = first_page.get("ids") if isinstance(first_page, dict) else None
        entities = first_page.get("entities") if isinstance(first_page, dict) else None

        if not isinstance(ids, list) or not isinstance(entities, dict):
            raise ScraperParseError("Domclick __SSR_STATE__ missing search.pages['0']")

        parsed_at = datetime.now(timezone.utc)
        city = _extract_city_from_url(self.base_url)
        listings: list[ScrapedListingDTO] = []
        for entity_id in ids:
            entity = entities.get(str(entity_id))
            if not isinstance(entity, dict):
                continue
            listing = self._parse_entity(entity=entity, parsed_at=parsed_at, city=city)
            if listing is not None:
                listings.append(listing)

        if not listings:
            raise ScraperParseError("Domclick __SSR_STATE__ does not contain parseable offers")
        return listings

    def _parse_entity(
        self,
        *,
        entity: dict[str, Any],
        parsed_at: datetime,
        city: str | None,
    ) -> ScrapedListingDTO | None:
        external_id = _to_string(entity.get("id"))
        path = _to_string(entity.get("path"))
        if external_id is None or path is None:
            return None

        image_url = None
        photos = entity.get("photos")
        if isinstance(photos, list) and photos and isinstance(photos[0], dict):
            image_url = _to_string(photos[0].get("url"))
            if image_url is not None:
                image_url = urljoin(self.base_url, image_url)

        title = _build_title(entity)
        published_at = _to_datetime(entity.get("publishedDate") or entity.get("updatedDate"))
        offer_region = _to_string(entity.get("offerRegionName"))
        object_info = entity.get("objectInfo") if isinstance(entity.get("objectInfo"), dict) else {}
        house = entity.get("house") if isinstance(entity.get("house"), dict) else {}

        return ScrapedListingDTO(
            external_id=external_id,
            url=urljoin(self.base_url, path),
            image_url=image_url,
            published_at=published_at,
            parsed_at=parsed_at,
            title=title,
            city=offer_region or city,
            price=_to_int(entity.get("price")),
            rooms=_to_int(object_info.get("rooms") or entity.get("roomsOffered")),
            area=_to_float(object_info.get("area")),
            floor=_to_int(object_info.get("floor")),
            data={
                "creator_type": "owner" if entity.get("isOwner") else "agency",
                "build_year": _to_int(house.get("buildYear")),
                "has_furniture": None,
                "property_type": _to_string(entity.get("offerType")),
                "living_conditions": [],
                "source_payload": entity,
            },
        )


def _extract_ssr_state(html: str) -> dict[str, Any]:
    marker = "window.__SSR_STATE__="
    start = html.find(marker)
    if start == -1:
        raise ScraperParseError("Domclick __SSR_STATE__ was not found")

    json_start = html.find("{", start)
    if json_start == -1:
        raise ScraperParseError("Domclick __SSR_STATE__ is malformed")

    raw = _read_balanced_object(html, json_start)
    normalized = raw.replace("undefined", "null")
    try:
        decoded = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise ScraperParseError("Cannot decode Domclick __SSR_STATE__") from exc
    if not isinstance(decoded, dict):
        raise ScraperParseError("Domclick __SSR_STATE__ has unexpected format")
    return decoded


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

    raise ScraperParseError("Domclick __SSR_STATE__ is incomplete")


def _extract_city_from_url(base_url: str) -> str | None:
    host = urlparse(base_url).hostname or ""
    parts = host.split(".")
    if len(parts) >= 3 and parts[0]:
        return parts[0]
    return None


def _to_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(str(value).replace(" ", "")))
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def _to_datetime(value: Any) -> datetime | None:
    raw = _to_string(value)
    if raw is None:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _build_title(entity: dict[str, Any]) -> str:
    object_info = entity.get("objectInfo") if isinstance(entity.get("objectInfo"), dict) else {}
    rooms = _to_int(object_info.get("rooms") or entity.get("roomsOffered"))
    area = _to_float(object_info.get("area"))
    floor = _to_int(object_info.get("floor"))
    floors = _to_int(object_info.get("floors") or entity.get("floors"))

    parts: list[str] = []
    if rooms is not None:
        parts.append(f"{rooms}-к квартира")
    if area is not None:
        area_text = int(area) if area.is_integer() else area
        parts.append(f"{area_text} м²")
    if floor is not None and floors is not None:
        parts.append(f"{floor}/{floors} эт.")
    elif floor is not None:
        parts.append(f"{floor} эт.")

    return ", ".join(parts) or f"Domclick listing {_to_string(entity.get('id')) or ''}".strip()
