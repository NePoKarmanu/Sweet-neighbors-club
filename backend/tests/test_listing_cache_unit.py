from __future__ import annotations

import unittest

from backend.core.listing_cache import ListingListCache
from backend.dto.listings import ListingSearchDTO


class ListingCacheUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cache = ListingListCache(redis_client=None, enabled=True, ttl_seconds=600)

    def test_build_cache_key_accepts_no_filters_preset(self) -> None:
        key = self.cache.build_cache_key(
            limit=20,
            offset=0,
            search=ListingSearchDTO(),
            sort_by=None,
            sort_order=None,
        )

        self.assertIsNotNone(key)
        self.assertIn("no_filters", key)
        self.assertIn("sort=default", key)

    def test_build_cache_key_accepts_price_max_20000_preset(self) -> None:
        key = self.cache.build_cache_key(
            limit=20,
            offset=0,
            search=ListingSearchDTO.model_validate({"price": {"max": 20000}}),
            sort_by="price",
            sort_order="asc",
        )

        self.assertIsNotNone(key)
        self.assertIn("price_max_20000", key)
        self.assertIn("sort=price:asc", key)

    def test_build_cache_key_accepts_creator_type_preset(self) -> None:
        owner_key = self.cache.build_cache_key(
            limit=20,
            offset=0,
            search=ListingSearchDTO.model_validate({"creator_types": ["owner"]}),
            sort_by="published_at",
            sort_order="desc",
        )
        agency_key = self.cache.build_cache_key(
            limit=20,
            offset=0,
            search=ListingSearchDTO.model_validate({"creator_types": ["agency"]}),
            sort_by="published_at",
            sort_order="desc",
        )

        self.assertIsNotNone(owner_key)
        self.assertIsNotNone(agency_key)
        self.assertIn("creator_owner", owner_key)
        self.assertIn("creator_agency", agency_key)

    def test_build_cache_key_rejects_non_first_page_and_non_hot_filters(self) -> None:
        key_with_offset = self.cache.build_cache_key(
            limit=20,
            offset=1,
            search=ListingSearchDTO(),
            sort_by=None,
            sort_order=None,
        )
        key_with_irrelevant_search = self.cache.build_cache_key(
            limit=20,
            offset=0,
            search=ListingSearchDTO.model_validate({"rooms": {"min": 1}}),
            sort_by=None,
            sort_order=None,
        )

        self.assertIsNone(key_with_offset)
        self.assertIsNone(key_with_irrelevant_search)

    def test_build_cache_key_includes_limit_and_sorting(self) -> None:
        key_default = self.cache.build_cache_key(
            limit=20,
            offset=0,
            search=ListingSearchDTO(),
            sort_by=None,
            sort_order=None,
        )
        key_price_desc = self.cache.build_cache_key(
            limit=50,
            offset=0,
            search=ListingSearchDTO(),
            sort_by="price",
            sort_order="desc",
        )

        self.assertNotEqual(key_default, key_price_desc)
        self.assertIn("limit=20", key_default)
        self.assertIn("limit=50", key_price_desc)
        self.assertIn("sort=price:desc", key_price_desc)


if __name__ == "__main__":
    unittest.main()
