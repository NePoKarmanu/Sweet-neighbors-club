from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import MagicMock, patch

from backend.db.repositories.search_filters import SearchFilterRepository

if "jwt" not in sys.modules:
    jwt_module = types.ModuleType("jwt")
    jwt_module.InvalidTokenError = Exception
    sys.modules["jwt"] = jwt_module

if "pywebpush" not in sys.modules:
    pywebpush_module = types.ModuleType("pywebpush")
    pywebpush_module.WebPushException = Exception
    pywebpush_module.webpush = lambda *args, **kwargs: None
    sys.modules["pywebpush"] = pywebpush_module

from backend.services.deliveries import email_sender, push_sender


class DeliverySendersAndFiltersUnitTests(unittest.TestCase):
    def test_email_sender_uses_timeout_and_tls_handshake(self) -> None:
        smtp_client = MagicMock()
        smtp_ctx = MagicMock()
        smtp_ctx.__enter__.return_value = smtp_client
        smtp_ctx.__exit__.return_value = False

        with (
            patch.object(email_sender.settings, "SMTP_HOST", "smtp.example.com"),
            patch.object(email_sender.settings, "SMTP_PORT", 587),
            patch.object(email_sender.settings, "SMTP_FROM", "noreply@example.com"),
            patch.object(email_sender.settings, "SMTP_USE_TLS", True),
            patch.object(email_sender.settings, "SMTP_USERNAME", "user"),
            patch.object(email_sender.settings, "SMTP_PASSWORD", "pass"),
            patch("backend.services.deliveries.email_sender.smtplib.SMTP", return_value=smtp_ctx) as smtp_ctor,
        ):
            email_sender.EmailSender().send(
                recipient="to@example.com",
                title="Flat",
                url="https://example.com/flat",
                price=10000.0,
            )

        smtp_ctor.assert_called_once_with("smtp.example.com", 587, timeout=15)
        self.assertEqual(smtp_client.ehlo.call_count, 2)
        smtp_client.starttls.assert_called_once()
        smtp_client.login.assert_called_once_with("user", "pass")
        smtp_client.send_message.assert_called_once()

    def test_push_sender_does_not_require_public_key_for_server_send(self) -> None:
        subscription = MagicMock(endpoint="https://push.example.com/ok", p256dh="p", auth="a")
        with (
            patch.object(push_sender.settings, "WEB_PUSH_VAPID_PRIVATE_KEY", "private"),
            patch.object(push_sender.settings, "WEB_PUSH_VAPID_PUBLIC_KEY", None),
            patch.object(push_sender.settings, "WEB_PUSH_VAPID_CLAIMS_SUBJECT", "mailto:test@example.com"),
            patch("backend.services.deliveries.push_sender.webpush") as webpush_mock,
        ):
            push_sender.PushSender().send(
                push_subscription=subscription,
                title="Flat",
                url="https://example.com/flat",
                price=10000.0,
            )
        webpush_mock.assert_called_once()

    def test_active_subscriptions_query_contains_date_window(self) -> None:
        session = MagicMock()
        session.execute.return_value.all.return_value = []
        repo = SearchFilterRepository(session)

        repo.list_active_with_subscriptions()

        query = session.execute.call_args[0][0]
        query_str = str(query)
        self.assertIn("subscriptions.start_date", query_str)
        self.assertIn("subscriptions.end_date", query_str)


if __name__ == "__main__":
    unittest.main()
