from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from backend.db.repositories.listings import ListingUpsertResult
from backend.scrapers.runner import run_all_scrapers


class ScraperRunnerCacheInvalidationUnitTests(unittest.TestCase):
    def test_invalidate_cache_after_successful_upsert(self) -> None:
        db = MagicMock()
        scraper = SimpleNamespace(
            aggregator_name="cian",
            base_url="https://example.com",
            scrape=lambda: [SimpleNamespace(to_repository_payload=lambda: {"external_id": "1", "url": "u", "title": "t"})],
        )

        with (
            patch("backend.scrapers.runner.load_scrapers", return_value=[scraper]),
            patch("backend.scrapers.runner.AggregatorRepository") as aggregator_repo_cls,
            patch("backend.scrapers.runner.ListingRepository") as listing_repo_cls,
            patch("backend.scrapers.runner.invalidate_listing_list_cache") as invalidate_cache,
        ):
            aggregator_repo_cls.return_value.get_or_create.return_value = SimpleNamespace(id=1)
            listing_repo_cls.return_value.upsert_many.return_value = ListingUpsertResult(created=0, updated=0)

            run_all_scrapers(db, provider_name=None)

        invalidate_cache.assert_called_once()

    def test_does_not_invalidate_cache_when_all_providers_fail(self) -> None:
        db = MagicMock()
        scraper = SimpleNamespace(
            aggregator_name="cian",
            base_url="https://example.com",
            scrape=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        with (
            patch("backend.scrapers.runner.load_scrapers", return_value=[scraper]),
            patch("backend.scrapers.runner.AggregatorRepository") as aggregator_repo_cls,
            patch("backend.scrapers.runner.ListingRepository"),
            patch("backend.scrapers.runner.invalidate_listing_list_cache") as invalidate_cache,
        ):
            aggregator_repo_cls.return_value.get_or_create.return_value = SimpleNamespace(id=1)

            run_all_scrapers(db, provider_name=None)

        invalidate_cache.assert_not_called()


if __name__ == "__main__":
    unittest.main()
