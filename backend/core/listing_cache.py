from __future__ import annotations

from functools import lru_cache
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from backend.core.config import settings
from backend.dto.listings import ListingSearchDTO, ListingSortBy, ListingSortOrder
from backend.schemas.listings import ListingListResponse

LISTING_CACHE_NAMESPACE = "listing:list:v1"
LISTING_CACHE_PATTERN = f"{LISTING_CACHE_NAMESPACE}:*"


def _prune_empty_values(value: Any) -> Any:
    if isinstance(value, dict):
        pruned = {
            key: _prune_empty_values(item)
            for key, item in value.items()
        }
        return {
            key: item for key, item in pruned.items()
            if item not in (None, {}, [])
        }
    if isinstance(value, list):
        pruned_list = [_prune_empty_values(item) for item in value]
        return [item for item in pruned_list if item not in (None, {}, [])]
    return value


@lru_cache(maxsize=1)
def _get_redis_client() -> Redis | None:
    try:
        return Redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        return None


class ListingListCache:
    def __init__(
        self,
        *,
        redis_client: Redis | None = None,
        enabled: bool | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        self._redis = redis_client if redis_client is not None else _get_redis_client()
        self._enabled = settings.LISTING_CACHE_ENABLED if enabled is None else enabled
        configured_ttl = settings.LISTING_CACHE_TTL_SECONDS if ttl_seconds is None else ttl_seconds
        self._ttl_seconds = max(1, int(configured_ttl))

    def _is_available(self) -> bool:
        return self._enabled and self._redis is not None

    def build_cache_key(
        self,
        *,
        limit: int,
        offset: int,
        search: ListingSearchDTO,
        sort_by: ListingSortBy | None,
        sort_order: ListingSortOrder | None,
    ) -> str | None:
        if offset != 0:
            return None

        normalized_search = _prune_empty_values(search.model_dump(exclude_none=True))
        preset_name = self._detect_preset(normalized_search)
        if preset_name is None:
            return None

        if sort_by is None and sort_order is None:
            sort_token = "default"
        else:
            sort_token = f"{sort_by}:{sort_order}"

        return f"{LISTING_CACHE_NAMESPACE}:{preset_name}:sort={sort_token}:limit={limit}"

    def _detect_preset(self, normalized_search: dict[str, Any]) -> str | None:
        if not normalized_search:
            return "no_filters"

        if normalized_search == {"price": {"max": 20000}}:
            return "price_max_20000"

        creator_types = normalized_search.get("creator_types")
        if isinstance(creator_types, list) and len(creator_types) == 1:
            creator_type = creator_types[0]
            if creator_type in {"owner", "agency"} and normalized_search == {"creator_types": [creator_type]}:
                return f"creator_{creator_type}"

        return None

    def get_cached_response(self, cache_key: str) -> ListingListResponse | None:
        if not self._is_available():
            return None
        try:
            payload = self._redis.get(cache_key)
            if payload is None:
                return None
            return ListingListResponse.model_validate_json(payload)
        except (RedisError, ValueError):
            return None

    def set_cached_response(self, cache_key: str, response: ListingListResponse) -> None:
        if not self._is_available():
            return
        try:
            self._redis.setex(cache_key, self._ttl_seconds, response.model_dump_json())
        except RedisError:
            return

    def clear_namespace(self) -> None:
        if not self._is_available():
            return
        try:
            keys = list(self._redis.scan_iter(match=LISTING_CACHE_PATTERN))
            if keys:
                self._redis.delete(*keys)
        except RedisError:
            return


def invalidate_listing_list_cache() -> None:
    ListingListCache().clear_namespace()
