from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import types
import unittest
from unittest.mock import MagicMock, patch

from backend.scrapers.runner import ScrapeRunResult, ScraperRunError

if "backend.db.session" not in sys.modules:
    session_module = types.ModuleType("backend.db.session")
    session_module.SessionLocal = lambda: None
    sys.modules["backend.db.session"] = session_module

_SCRAPING_MODULE_PATH = Path(__file__).resolve().parents[1] / "tasks" / "scraping.py"
_SCRAPING_MODULE_SPEC = importlib.util.spec_from_file_location(
    "backend.tasks.scraping_under_test",
    _SCRAPING_MODULE_PATH,
)
if _SCRAPING_MODULE_SPEC is None or _SCRAPING_MODULE_SPEC.loader is None:
    raise RuntimeError("Failed to load scraping task module for tests")
scraping_module = importlib.util.module_from_spec(_SCRAPING_MODULE_SPEC)
_SCRAPING_MODULE_SPEC.loader.exec_module(scraping_module)
run_all_scrapers_task = scraping_module.run_all_scrapers_task


class ScrapingTaskTests(unittest.TestCase):
    def test_run_all_scrapers_task_serializes_result(self) -> None:
        mock_db = MagicMock()
        result_model = ScrapeRunResult(
            created=2,
            updated=1,
            failed=1,
            requested_provider="cian",
            executed_providers=["cian"],
            errors=[ScraperRunError(aggregator_name="cian", message="sample error")],
        )

        with (
            patch.object(scraping_module, "SessionLocal", return_value=mock_db),
            patch.object(scraping_module, "run_all_scrapers", return_value=result_model),
            patch.object(scraping_module, "logger") as logger_mock,
        ):
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
        self.assertEqual(logger_mock.info.call_count, 2)
        start_extra = logger_mock.info.call_args_list[0].kwargs.get("extra", {})
        finish_extra = logger_mock.info.call_args_list[1].kwargs.get("extra", {})
        self.assertEqual(start_extra.get("event"), "scraping.task_started")
        self.assertEqual(finish_extra.get("event"), "scraping.task_finished")
        mock_db.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
