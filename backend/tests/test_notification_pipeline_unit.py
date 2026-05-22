from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

from backend.db.models.enums import NotificationChannel

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

if "pywebpush" not in sys.modules:
    pywebpush_module = types.ModuleType("pywebpush")
    pywebpush_module.WebPushException = Exception
    pywebpush_module.webpush = lambda *args, **kwargs: None
    sys.modules["pywebpush"] = pywebpush_module

_PIPELINE_MODULE_PATH = Path(__file__).resolve().parents[1] / "services" / "notification_pipeline.py"
if "backend.services" not in sys.modules:
    services_package = types.ModuleType("backend.services")
    services_package.__path__ = [str(_PIPELINE_MODULE_PATH.parent)]
    sys.modules["backend.services"] = services_package
_PIPELINE_MODULE_SPEC = importlib.util.spec_from_file_location(
    "backend.services.notification_pipeline_under_test",
    _PIPELINE_MODULE_PATH,
)
if _PIPELINE_MODULE_SPEC is None or _PIPELINE_MODULE_SPEC.loader is None:
    raise RuntimeError("Failed to load notification pipeline module for tests")
notification_pipeline = importlib.util.module_from_spec(_PIPELINE_MODULE_SPEC)
_PIPELINE_MODULE_SPEC.loader.exec_module(notification_pipeline)


class NotificationPipelineUnitTests(unittest.TestCase):
    def test_fits_range_none_bounds_are_unbounded(self) -> None:
        self.assertTrue(notification_pipeline._fits_range(10, None, None))
        self.assertTrue(notification_pipeline._fits_range(10, None, 20))
        self.assertTrue(notification_pipeline._fits_range(10, 5, None))
        self.assertFalse(notification_pipeline._fits_range(10, 11, None))
        self.assertFalse(notification_pipeline._fits_range(10, None, 9))

    def test_process_delivery_group_logs_success_for_email(self) -> None:
        group = [
            (
                SimpleNamespace(id=1, notification_id=101, channel=NotificationChannel.email),
                SimpleNamespace(id=101, listing_id=1001, user_id=7),
            )
        ]
        users_by_id = {7: SimpleNamespace(id=7, email="user@example.com")}
        listings_by_id = {1001: SimpleNamespace(id=1001, title="Flat", url="https://example.com/1", price=12000)}

        delivery_repository = MagicMock()
        push_repository = MagicMock()
        sent_listing_repository = MagicMock()
        email_sender = MagicMock()
        push_sender = MagicMock()

        with patch.object(notification_pipeline, "logger") as logger_mock:
            processed, pending_changes = notification_pipeline._process_delivery_group(
                group=group,
                target_user_id=7,
                channel=NotificationChannel.email,
                now=datetime.now(timezone.utc),
                users_by_id=users_by_id,
                listings_by_id=listings_by_id,
                active_push_subscriptions_by_user_id={},
                delivery_repository=delivery_repository,
                push_repository=push_repository,
                sent_listing_repository=sent_listing_repository,
                email_sender=email_sender,
                push_sender=push_sender,
            )

        self.assertEqual(processed, 1)
        self.assertEqual(pending_changes, 2)
        email_sender.send_many.assert_called_once()
        self.assertEqual(email_sender.send_many.call_args.kwargs.get("user_id"), 7)
        delivery_repository.mark_sent.assert_called_once()
        sent_listing_repository.create_if_missing.assert_called_once()
        self.assertTrue(
            any(
                call.kwargs.get("extra", {}).get("event") == "notifications.delivery_send_attempt"
                for call in logger_mock.info.call_args_list
            )
        )
        self.assertTrue(
            any(
                call.kwargs.get("extra", {}).get("event") == "notifications.delivery_send_success"
                for call in logger_mock.info.call_args_list
            )
        )

    def test_process_delivery_group_webpush_410_logs_and_deactivates_subscription(self) -> None:
        group = [
            (
                SimpleNamespace(id=1, notification_id=201, channel=NotificationChannel.push),
                SimpleNamespace(id=201, listing_id=2001, user_id=11),
            )
        ]
        users_by_id = {11: SimpleNamespace(id=11, email="user@example.com")}
        listings_by_id = {2001: SimpleNamespace(id=2001, title="Flat", url="https://example.com/2", price=15000)}
        push_subscription = SimpleNamespace(endpoint="https://push.example.com/bad", p256dh="p", auth="a")

        delivery_repository = MagicMock()
        push_repository = MagicMock()
        sent_listing_repository = MagicMock()
        email_sender = MagicMock()
        push_sender = MagicMock()

        class DummyWebPushException(Exception):
            def __init__(self, message: str, status_code: int) -> None:
                super().__init__(message)
                self.response = SimpleNamespace(status_code=status_code)

        push_sender.send_many.side_effect = DummyWebPushException("gone", 410)

        with (
            patch.object(notification_pipeline, "WebPushException", DummyWebPushException),
            patch.object(notification_pipeline, "logger") as logger_mock,
        ):
            processed, pending_changes = notification_pipeline._process_delivery_group(
                group=group,
                target_user_id=11,
                channel=NotificationChannel.push,
                now=datetime.now(timezone.utc),
                users_by_id=users_by_id,
                listings_by_id=listings_by_id,
                active_push_subscriptions_by_user_id={11: push_subscription},
                delivery_repository=delivery_repository,
                push_repository=push_repository,
                sent_listing_repository=sent_listing_repository,
                email_sender=email_sender,
                push_sender=push_sender,
            )

        self.assertEqual(processed, 1)
        self.assertEqual(pending_changes, 1)
        delivery_repository.rollback.assert_called_once()
        push_repository.deactivate_by_endpoint.assert_called_once_with(endpoint="https://push.example.com/bad")
        delivery_repository.mark_failed.assert_called_once()
        self.assertTrue(
            any(
                call.kwargs.get("extra", {}).get("event") == "notifications.delivery_send_webpush_failed"
                and call.kwargs.get("extra", {}).get("deactivated_subscription") is True
                for call in logger_mock.warning.call_args_list
            )
        )
        self.assertTrue(
            any(
                call.kwargs.get("extra", {}).get("event") == "notifications.delivery_send_failed"
                for call in logger_mock.exception.call_args_list
            )
        )


if __name__ == "__main__":
    unittest.main()
