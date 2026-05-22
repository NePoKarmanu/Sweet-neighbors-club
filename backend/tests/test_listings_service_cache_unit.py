from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

if "jwt" not in sys.modules:
    jwt_module = types.ModuleType("jwt")
    jwt_module.InvalidTokenError = Exception
    sys.modules["jwt"] = jwt_module

from backend.schemas.listings import ListingListResponse

_LISTINGS_MODULE_PATH = Path(__file__).resolve().parents[1] / "services" / "listings.py"
_LISTINGS_MODULE_SPEC = importlib.util.spec_from_file_location(
    "backend.services.listings_under_test",
    _LISTINGS_MODULE_PATH,
)
if _LISTINGS_MODULE_SPEC is None or _LISTINGS_MODULE_SPEC.loader is None:
    raise RuntimeError("Failed to load listings module for tests")
listings_module = importlib.util.module_from_spec(_LISTINGS_MODULE_SPEC)
_LISTINGS_MODULE_SPEC.loader.exec_module(listings_module)
list_listings = listings_module.list_listings


class ListingsServiceCacheUnitTests(unittest.TestCase):
    def test_cache_hit_returns_cached_response_without_repository_call(self) -> None:
        db = MagicMock()
        cached_response = ListingListResponse(
            items=[],
            total=0,
            limit=20,
            offset=0,
            has_more=False,
        )

        with (
            patch.object(listings_module, "ListingListCache") as cache_cls,
            patch.object(listings_module, "ListingRepository") as repository_cls,
            patch.object(listings_module, "logger") as logger_mock,
        ):
            cache = cache_cls.return_value
            cache.build_cache_key.return_value = "listing:list:v1:no_filters:sort=default:limit=20"
            cache.get_cached_response.return_value = cached_response
            cache._is_available.return_value = True

            result = list_listings(
                db=db,
                limit=20,
                offset=0,
                search=None,
                sort_by=None,
                sort_order=None,
            )

        self.assertEqual(result, cached_response)
        repository_cls.assert_not_called()
        cache.set_cached_response.assert_not_called()
        self.assertTrue(
            any(
                call.kwargs.get("extra", {}).get("source") == "cache"
                for call in logger_mock.info.call_args_list
            )
        )

    def test_cache_miss_queries_repository_and_populates_cache(self) -> None:
        db = MagicMock()
        item = SimpleNamespace(
            id=1,
            aggregator_id=1,
            external_id="ext-1",
            url="https://example.com/1",
            image_url=None,
            published_at=None,
            parsed_at=None,
            title="Listing 1",
            price=12000,
            rooms=1,
            area=32.5,
            floor=2,
            data={"creator_type": "owner", "living_conditions": []},
        )

        with (
            patch.object(listings_module, "ListingListCache") as cache_cls,
            patch.object(listings_module, "ListingRepository") as repository_cls,
            patch.object(listings_module, "logger") as logger_mock,
        ):
            cache = cache_cls.return_value
            cache.build_cache_key.return_value = "listing:list:v1:no_filters:sort=default:limit=20"
            cache.get_cached_response.return_value = None
            cache._is_available.return_value = True

            repository = repository_cls.return_value
            repository.list_with_filters.return_value = ([item], 1)

            result = list_listings(
                db=db,
                limit=20,
                offset=0,
                search=None,
                sort_by=None,
                sort_order=None,
            )

        self.assertEqual(result.total, 1)
        self.assertEqual(len(result.items), 1)
        repository.list_with_filters.assert_called_once()
        cache.set_cached_response.assert_called_once()
        self.assertTrue(
            any(
                call.kwargs.get("extra", {}).get("source") == "db"
                and call.kwargs.get("extra", {}).get("reason") == "cache_miss"
                for call in logger_mock.info.call_args_list
            )
        )

    def test_cache_read_error_falls_back_to_repository(self) -> None:
        db = MagicMock()
        item = SimpleNamespace(
            id=1,
            aggregator_id=1,
            external_id="ext-1",
            url="https://example.com/1",
            image_url=None,
            published_at=None,
            parsed_at=None,
            title="Listing 1",
            price=12000,
            rooms=1,
            area=32.5,
            floor=2,
            data={},
        )

        with (
            patch.object(listings_module, "ListingListCache") as cache_cls,
            patch.object(listings_module, "ListingRepository") as repository_cls,
            patch.object(listings_module, "logger") as logger_mock,
        ):
            cache = cache_cls.return_value
            cache.build_cache_key.return_value = "listing:list:v1:no_filters:sort=default:limit=20"
            cache.get_cached_response.side_effect = RuntimeError("redis unavailable")
            cache._is_available.return_value = True

            repository = repository_cls.return_value
            repository.list_with_filters.return_value = ([item], 1)

            result = list_listings(
                db=db,
                limit=20,
                offset=0,
                search=None,
                sort_by=None,
                sort_order=None,
            )

        self.assertEqual(result.total, 1)
        repository.list_with_filters.assert_called_once()
        self.assertTrue(
            any(
                call.kwargs.get("extra", {}).get("reason") == "cache_read_error"
                for call in logger_mock.exception.call_args_list
            )
        )


if __name__ == "__main__":
    unittest.main()
