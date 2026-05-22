from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import types
import unittest
from unittest.mock import MagicMock, patch

if "backend.db.session" not in sys.modules:
    session_module = types.ModuleType("backend.db.session")
    session_module.SessionLocal = lambda: None
    sys.modules["backend.db.session"] = session_module

if "backend.services" not in sys.modules:
    services_package = types.ModuleType("backend.services")
    services_package.__path__ = [str((Path(__file__).resolve().parents[1] / "services"))]
    sys.modules["backend.services"] = services_package

if "backend.services.notification_pipeline" not in sys.modules:
    pipeline_module = types.ModuleType("backend.services.notification_pipeline")
    pipeline_module.match_listings_to_subscriptions = lambda *args, **kwargs: 0
    pipeline_module.materialize_pending_deliveries = lambda *args, **kwargs: 0
    pipeline_module.process_pending_deliveries = lambda *args, **kwargs: 0
    sys.modules["backend.services.notification_pipeline"] = pipeline_module

_NOTIFICATIONS_MODULE_PATH = Path(__file__).resolve().parents[1] / "tasks" / "notifications.py"
_NOTIFICATIONS_MODULE_SPEC = importlib.util.spec_from_file_location(
    "backend.tasks.notifications_under_test",
    _NOTIFICATIONS_MODULE_PATH,
)
if _NOTIFICATIONS_MODULE_SPEC is None or _NOTIFICATIONS_MODULE_SPEC.loader is None:
    raise RuntimeError("Failed to load notifications task module for tests")
notifications_module = importlib.util.module_from_spec(_NOTIFICATIONS_MODULE_SPEC)
_NOTIFICATIONS_MODULE_SPEC.loader.exec_module(notifications_module)
run_full_pipeline_task = notifications_module.run_full_pipeline_task


class NotificationsTaskTests(unittest.TestCase):
    def test_run_full_pipeline_task_returns_aggregated_result(self) -> None:
        mock_db = MagicMock()

        with (
            patch.object(notifications_module, "SessionLocal", return_value=mock_db),
            patch.object(notifications_module, "match_listings_to_subscriptions", return_value=7),
            patch.object(notifications_module, "materialize_pending_deliveries", return_value=5),
            patch.object(notifications_module, "process_pending_deliveries", return_value=4),
            patch.object(notifications_module, "logger") as logger_mock,
        ):
            result = run_full_pipeline_task.run()

        self.assertEqual(
            result,
            {
                "created_notifications": 7,
                "created_deliveries": 5,
                "processed_deliveries": 4,
                "user_id": None,
            },
        )
        self.assertEqual(logger_mock.info.call_count, 2)
        start_extra = logger_mock.info.call_args_list[0].kwargs.get("extra", {})
        finish_extra = logger_mock.info.call_args_list[1].kwargs.get("extra", {})
        self.assertEqual(start_extra.get("event"), "notifications.task_started")
        self.assertEqual(finish_extra.get("event"), "notifications.task_finished")
        mock_db.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
