from __future__ import annotations

from datetime import datetime, timezone
import unittest

from backend.scrapers.base import ScraperProviderNotFoundError
from backend.scrapers.providers.avito import AvitoScraper
from backend.scrapers.providers.cian import CianScraper
from backend.scrapers.registry import load_scrapers


class ScraperRegistryTests(unittest.TestCase):
    def test_load_scrapers_finds_providers(self) -> None:
        scrapers = load_scrapers()
        provider_names = {scraper.aggregator_name for scraper in scrapers}

        self.assertIn("cian", provider_names)
        self.assertIn("avito", provider_names)

    def test_load_scrapers_filters_by_provider(self) -> None:
        scrapers = load_scrapers(provider_name="  CIAN ")

        self.assertEqual(len(scrapers), 1)
        self.assertEqual(scrapers[0].aggregator_name, "cian")

    def test_load_scrapers_raises_for_unknown_provider(self) -> None:
        with self.assertRaises(ScraperProviderNotFoundError):
            load_scrapers(provider_name="unknown_provider")

    def test_load_scrapers_filters_by_avito_provider(self) -> None:
        scrapers = load_scrapers(provider_name=" avito ")

        self.assertEqual(len(scrapers), 1)
        self.assertEqual(scrapers[0].aggregator_name, "avito")


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
                      "formattedFullInfo": "2-room flat · 45.5 m² · 4/9 floor",
                      "price": {"value": 15000},
                      "roomsCount": 2,
                      "totalArea": 45.5,
                      "floorNumber": 4,
                      "publishedAt": "2026-04-24T11:04:58+00:00",
                      "isByHomeowner": false,
                      "hasFurniture": true,
                      "buildYear": 2005,
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
        self.assertEqual(listing.title, "2-room flat · 45.5 m² · 4/9 floor")
        self.assertEqual(listing.data["creator_type"], "agency")
        self.assertEqual(listing.data["has_furniture"], True)

    def test_extract_creator_type(self) -> None:
        owner_offer = {"id": 1, "isByHomeowner": True}
        agency_offer = {"id": 2, "isByHomeowner": False}
        null_homeowner_offer = {"id": 3, "isByHomeowner": None}

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
        self.assertEqual(null_homeowner_listing.data["creator_type"], "owner")


class AvitoScraperTests(unittest.TestCase):
    def test_build_headers_applies_runtime_overrides(self) -> None:
        scraper = AvitoScraper(cookie="cookie=2", user_agent="custom-avito-agent")

        headers = scraper._build_headers()

        self.assertEqual(headers["Cookie"], "cookie=2")
        self.assertEqual(headers["User-Agent"], "custom-avito-agent")

    def test_parse_item_cards(self) -> None:
        html = """
        <html>
          <body>
            <div data-marker="item" data-item-id="1001">
              <a data-marker="item-title" href="/voronezh/kvartiry/1-k._kvartira_40_m_39_et._1001">
                1-к. квартира, 40 м², 3/9 эт.
              </a>
              <meta itemprop="price" content="25000" />
              <img itemprop="image" src="https://example.org/image-1001.jpg" />
              <span data-marker="item-date">7 ноября 2025</span>
            </div>
            <div data-marker="item" data-item-id="1002">
              <a data-marker="item-title" href="/voronezh/kvartiry/kvartira-studiya_30_m_24_et._1002">
                Квартира-студия, 30 м², 2/4 эт.
              </a>
              <div data-marker="item-price">30 000 ₽ в месяц</div>
              <img itemprop="image" src="https://example.org/image-1002.jpg" />
              <span data-marker="item-date">1 час назад</span>
            </div>
          </body>
        </html>
        """

        listings = AvitoScraper().parse(html)

        self.assertEqual(len(listings), 2)

        first = listings[0]
        self.assertEqual(first.external_id, "1001")
        self.assertEqual(
            first.url,
            "https://www.avito.ru/voronezh/kvartiry/1-k._kvartira_40_m_39_et._1001",
        )
        self.assertEqual(first.title, "1-к. квартира, 40 м², 3/9 эт.")
        self.assertEqual(first.price, 25000)
        self.assertEqual(first.rooms, 1)
        self.assertEqual(first.area, 40)
        self.assertEqual(first.floor, 3)
        self.assertEqual(first.image_url, "https://example.org/image-1001.jpg")

        second = listings[1]
        self.assertEqual(second.external_id, "1002")
        self.assertEqual(second.rooms, 0)
        self.assertEqual(second.area, 30)
        self.assertEqual(second.floor, 2)
        self.assertEqual(second.price, 30000)
        self.assertIsNotNone(second.published_at)


if __name__ == "__main__":
    unittest.main()
