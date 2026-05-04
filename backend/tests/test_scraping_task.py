from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from backend.scrapers.runner import ScrapeRunResult, ScraperRunError
from backend.tasks.scraping import run_all_scrapers_task


class ScrapingTaskTests(unittest.TestCase):
    @patch("backend.tasks.scraping.SessionLocal")
    @patch("backend.tasks.scraping.run_all_scrapers")
    def test_run_all_scrapers_task_serializes_result(
        self,
        mock_run_all_scrapers: MagicMock,
        mock_session_local: MagicMock,
    ) -> None:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_run_all_scrapers.return_value = ScrapeRunResult(
            created=2,
            updated=1,
            failed=1,
            requested_provider="cian",
            executed_providers=["cian"],
            errors=[ScraperRunError(aggregator_name="cian", message="sample error")],
        )

        result = run_all_scrapers_task.run(provider_name="cian")

        self.assertEqual(result["created"], 2)
        self.assertEqual(result["updated"], 1)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(result["requested_provider"], "cian")
        self.assertEqual(result["executed_providers"], ["cian"])
        self.assertEqual(
            result["errors"],
            [{"aggregator_name": "cian", "message": "sample error"}],
        )
        mock_db.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
