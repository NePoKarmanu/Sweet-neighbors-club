from __future__ import annotations

from datetime import datetime, timezone
import unittest

from backend.scrapers.base import ScraperProviderNotFoundError
from backend.scrapers.providers.cian import CianScraper
from backend.scrapers.registry import load_scrapers


class ScraperRegistryTests(unittest.TestCase):
    def test_load_scrapers_finds_cian_provider(self) -> None:
        scrapers = load_scrapers()

        self.assertIn("cian", {scraper.aggregator_name for scraper in scrapers})

    def test_load_scrapers_filters_by_provider(self) -> None:
        scrapers = load_scrapers(provider_name="  CIAN ")

        self.assertEqual(len(scrapers), 1)
        self.assertEqual(scrapers[0].aggregator_name, "cian")

    def test_load_scrapers_raises_for_unknown_provider(self) -> None:
        with self.assertRaises(ScraperProviderNotFoundError):
            load_scrapers(provider_name="unknown_provider")


class CianScraperTests(unittest.TestCase):
    def test_build_headers_applies_runtime_overrides(self) -> None:
        scraper = CianScraper(cookie="cookie=1", user_agent="custom-agent")

        headers = scraper._build_headers()

        self.assertEqual(headers["Cookie"], "cookie=1")
        self.assertEqual(headers["User-Agent"], "custom-agent")

    def test_parse_frontend_serp_state(self) -> None:
        html = """
        <html>
          <script>
            window._cianConfig['frontend-serp'] = {
              "defaultState": {
                "results": {
                  "offers": [
                    {
                      "id": 123,
                      "url": "/rent/flat/123/",
                      "title": "2-room flat",
                      "price": {"value": 15000},
                      "roomsCount": 2,
                      "totalArea": 45.5,
                      "floorNumber": 4,
                      "publishedAt": "2026-04-24T11:04:58+00:00",
                      "sellerType": "agency",
                      "buildYear": 2005,
                      "hasRepair": true,
                      "propertyType": "flat",
                      "livingConditions": ["furniture"]
                    }
                  ]
                }
              }
            };
          </script>
        </html>
        """

        listings = CianScraper().parse(html)

        self.assertEqual(len(listings), 1)
        listing = listings[0]
        self.assertEqual(listing.external_id, "123")
        self.assertEqual(listing.url, "https://voronezh.cian.ru/rent/flat/123/")
        self.assertEqual(listing.price, 15000)
        self.assertEqual(listing.rooms, 2)
        self.assertEqual(listing.area, 45.5)
        self.assertEqual(listing.floor, 4)
        self.assertEqual(listing.data["creator_type"], "agency")

    def test_extract_creator_type(self) -> None:
        owner_offer = {"id": 1, "isByHomeowner": True}
        agency_offer = {"id": 2, "isByHomeowner": False}
        null_homeowner_offer = {"id": 3, "isByHomeowner": None, "gaLabel": "deal=1;owner=0;spec=agent"}

        scraper = CianScraper()
        parsed_at = datetime.now(timezone.utc)

        owner_listing = scraper._parse_offer(owner_offer, parsed_at=parsed_at)
        agency_listing = scraper._parse_offer(agency_offer, parsed_at=parsed_at)
        null_homeowner_listing = scraper._parse_offer(null_homeowner_offer, parsed_at=parsed_at)

        self.assertIsNotNone(owner_listing)
        self.assertIsNotNone(agency_listing)
        self.assertIsNotNone(null_homeowner_listing)
        self.assertEqual(owner_listing.data["creator_type"], "owner")
        self.assertEqual(agency_listing.data["creator_type"], "agency")
        self.assertEqual(null_homeowner_listing.data["creator_type"], "agency")


if __name__ == "__main__":
    unittest.main()
