from __future__ import annotations

from datetime import date
import sys
from types import SimpleNamespace
import types
import unittest
from unittest.mock import MagicMock, patch

from backend.db.models.enums import NotificationChannel
from backend.db.models.subscriptions import Subscription

if "jwt" not in sys.modules:
    jwt_module = types.ModuleType("jwt")
    jwt_module.InvalidTokenError = Exception
    sys.modules["jwt"] = jwt_module

if "pywebpush" not in sys.modules:
    pywebpush_module = types.ModuleType("pywebpush")
    pywebpush_module.WebPushException = Exception
    pywebpush_module.webpush = lambda *args, **kwargs: None
    sys.modules["pywebpush"] = pywebpush_module

from backend.services import notification_pipeline


class NotificationPipelineUnitTests(unittest.TestCase):
    def test_fits_range_none_bounds_are_unbounded(self) -> None:
        self.assertTrue(notification_pipeline._fits_range(10, None, None))
        self.assertTrue(notification_pipeline._fits_range(10, None, 20))
        self.assertTrue(notification_pipeline._fits_range(10, 5, None))
        self.assertFalse(notification_pipeline._fits_range(10, 11, None))
        self.assertFalse(notification_pipeline._fits_range(10, None, 9))

    def test_match_listings_counter_counts_only_created_notifications(self) -> None:
        db = MagicMock()
        listing = SimpleNamespace(id=10, price=10000, rooms=1, area=30, floor=2, city="Voronezh", data={})
        search_filter = SimpleNamespace(
            city="Voronezh",
            price_min=None,
            price_max=None,
            rooms_min=None,
            rooms_max=None,
            area_min=None,
            area_max=None,
            floor_min=None,
            floor_max=None,
            additional_params={},
        )
        subscription = Subscription(
            user_id=1,
            start_date=date.today(),
            end_date=date.today(),
            notify_email=True,
            notify_push=True,
            is_active=True,
        )

        with (
            patch("backend.services.notification_pipeline.ListingRepository") as listing_repo_cls,
            patch("backend.services.notification_pipeline.SearchFilterRepository") as filter_repo_cls,
            patch("backend.services.notification_pipeline.NotificationRepository") as notification_repo_cls,
        ):
            listing_repo = listing_repo_cls.return_value
            filter_repo = filter_repo_cls.return_value
            notification_repo = notification_repo_cls.return_value
            listing_repo.list_recent_active.return_value = [listing]
            filter_repo.list_active_with_subscriptions.return_value = [(search_filter, subscription)]
            notification_repo.create_if_missing.side_effect = [SimpleNamespace(id=1), None]

            first_created = notification_pipeline.match_listings_to_subscriptions(db, batch_size=100)
            second_created = notification_pipeline.match_listings_to_subscriptions(db, batch_size=100)

        self.assertEqual(first_created, 1)
        self.assertEqual(second_created, 0)

    def test_matches_listing_checks_city(self) -> None:
        search_filter = SimpleNamespace(
            city="Voronezh",
            price_min=None,
            price_max=None,
            rooms_min=None,
            rooms_max=None,
            area_min=None,
            area_max=None,
            floor_min=None,
            floor_max=None,
            additional_params={},
        )
        listing_data = {"price": 10000, "rooms": 1, "area": 30, "floor": 2, "details": {"city": "Moscow"}}

        matches = notification_pipeline._matches_listing(search_filter, listing_data)

        self.assertFalse(matches)

    def test_process_push_410_deactivates_failing_endpoint(self) -> None:
        db = MagicMock()
        delivery = SimpleNamespace(notification_id=1, channel=NotificationChannel.push)
        notification = SimpleNamespace(listing_id=2, user_id=3)
        listing = SimpleNamespace(title="Flat", url="http://example.com/flat", price=12345)
        user = SimpleNamespace(id=3, email="user@example.com")
        push_subscription = SimpleNamespace(endpoint="https://push.example.com/bad", p256dh="k", auth="a")

        class DummyWebPushException(Exception):
            def __init__(self, message: str, status_code: int) -> None:
                super().__init__(message)
                self.response = SimpleNamespace(status_code=status_code)

        with (
            patch("backend.services.notification_pipeline.NotificationDeliveryRepository") as delivery_repo_cls,
            patch("backend.services.notification_pipeline.NotificationRepository") as notification_repo_cls,
            patch("backend.services.notification_pipeline.ListingRepository") as listing_repo_cls,
            patch("backend.services.notification_pipeline.UserRepository") as user_repo_cls,
            patch("backend.services.notification_pipeline.PushSubscriptionRepository") as push_repo_cls,
            patch("backend.services.notification_pipeline.SentListingRepository") as sent_repo_cls,
            patch("backend.services.notification_pipeline.EmailSender"),
            patch("backend.services.notification_pipeline.PushSender") as push_sender_cls,
            patch("backend.services.notification_pipeline.WebPushException", DummyWebPushException),
        ):
            delivery_repo = delivery_repo_cls.return_value
            notification_repo = notification_repo_cls.return_value
            listing_repo = listing_repo_cls.return_value
            user_repo = user_repo_cls.return_value
            push_repo = push_repo_cls.return_value
            push_sender = push_sender_cls.return_value
            sent_repo = sent_repo_cls.return_value

            delivery_repo.list_pending.return_value = [delivery]
            notification_repo.get_by_id.return_value = notification
            listing_repo.get_by_id.return_value = listing
            user_repo.get_by_id.return_value = user
            push_repo.get_any_active_for_user.return_value = push_subscription
            push_sender.send.side_effect = DummyWebPushException("gone", 410)

            processed = notification_pipeline.process_pending_deliveries(db, batch_size=10)

        self.assertEqual(processed, 1)
        push_repo.deactivate_by_endpoint.assert_called_once_with(endpoint="https://push.example.com/bad")
        delivery_repo.mark_failed.assert_called_once()
        sent_repo.create_if_missing.assert_not_called()

    def test_materialize_skips_push_channel_without_active_push_subscription(self) -> None:
        db = MagicMock()
        notification = SimpleNamespace(id=101, user_id=5)
        subscription = SimpleNamespace(user_id=5, notify_email=True, notify_push=True)

        with (
            patch("backend.services.notification_pipeline.NotificationRepository") as notification_repo_cls,
            patch("backend.services.notification_pipeline.SearchFilterRepository") as filter_repo_cls,
            patch("backend.services.notification_pipeline.NotificationDeliveryRepository") as delivery_repo_cls,
            patch("backend.services.notification_pipeline.PushSubscriptionRepository") as push_repo_cls,
        ):
            notification_repo = notification_repo_cls.return_value
            filter_repo = filter_repo_cls.return_value
            delivery_repo = delivery_repo_cls.return_value
            push_repo = push_repo_cls.return_value

            notification_repo.list_unprocessed.return_value = [notification]
            filter_repo.list_active_with_subscriptions.return_value = [(SimpleNamespace(), subscription)]
            push_repo.get_any_active_for_user.return_value = None
            delivery_repo.materialize_channels_for_notification.return_value = 1

            created = notification_pipeline.materialize_pending_deliveries(db, batch_size=100)

        self.assertEqual(created, 1)
        delivery_repo.materialize_channels_for_notification.assert_called_once_with(
            notification_id=101,
            include_email=True,
            include_push=False,
        )
    
    def test_process_pending_deliveries_large_batch_commits_in_chunks(self) -> None:
        db = MagicMock()
        deliveries = [SimpleNamespace(notification_id=i, channel=NotificationChannel.email) for i in range(1, 121)]

        with (
            patch("backend.services.notification_pipeline.NotificationDeliveryRepository") as delivery_repo_cls,
            patch("backend.services.notification_pipeline.NotificationRepository") as notification_repo_cls,
            patch("backend.services.notification_pipeline.ListingRepository") as listing_repo_cls,
            patch("backend.services.notification_pipeline.UserRepository") as user_repo_cls,
            patch("backend.services.notification_pipeline.PushSubscriptionRepository"),
            patch("backend.services.notification_pipeline.SentListingRepository") as sent_repo_cls,
            patch("backend.services.notification_pipeline.EmailSender"),
            patch("backend.services.notification_pipeline.PushSender"),
        ):
            delivery_repo = delivery_repo_cls.return_value
            notification_repo = notification_repo_cls.return_value
            listing_repo = listing_repo_cls.return_value
            user_repo = user_repo_cls.return_value
            sent_repo = sent_repo_cls.return_value

            delivery_repo.list_pending.return_value = deliveries
            notification_repo.get_by_id.side_effect = [
                SimpleNamespace(listing_id=i, user_id=1) for i in range(1, 121)
            ]
            listing_repo.get_by_id.side_effect = [
                SimpleNamespace(id=i, title=f"Listing {i}", url=f"http://example.com/{i}", price=1000 + i)
                for i in range(1, 121)
            ]
            user_repo.get_by_id.return_value = SimpleNamespace(id=1, email="user@example.com")

            processed = notification_pipeline.process_pending_deliveries(db, batch_size=200)

        self.assertEqual(processed, 120)
        self.assertEqual(delivery_repo.mark_sent.call_count, 120)
        self.assertEqual(delivery_repo.commit.call_count, 2)
        self.assertEqual(delivery_repo.flush.call_count, 2)
        self.assertEqual(sent_repo.create_if_missing.call_count, 120)

    def test_process_pending_deliveries_partial_failure_keeps_failed_and_continues(self) -> None:
        db = MagicMock()
        deliveries = [
            SimpleNamespace(notification_id=1, channel=NotificationChannel.email),
            SimpleNamespace(notification_id=2, channel=NotificationChannel.email),
        ]

        with (
            patch("backend.services.notification_pipeline.NotificationDeliveryRepository") as delivery_repo_cls,
            patch("backend.services.notification_pipeline.NotificationRepository") as notification_repo_cls,
            patch("backend.services.notification_pipeline.ListingRepository") as listing_repo_cls,
            patch("backend.services.notification_pipeline.UserRepository") as user_repo_cls,
            patch("backend.services.notification_pipeline.PushSubscriptionRepository"),
            patch("backend.services.notification_pipeline.SentListingRepository"),
            patch("backend.services.notification_pipeline.EmailSender") as email_sender_cls,
            patch("backend.services.notification_pipeline.PushSender"),
        ):
            delivery_repo = delivery_repo_cls.return_value
            notification_repo = notification_repo_cls.return_value
            listing_repo = listing_repo_cls.return_value
            user_repo = user_repo_cls.return_value
            email_sender = email_sender_cls.return_value

            delivery_repo.list_pending.return_value = deliveries
            notification_repo.get_by_id.side_effect = [
                SimpleNamespace(listing_id=101, user_id=1),
                SimpleNamespace(listing_id=202, user_id=2),
            ]
            listing_repo.get_by_id.side_effect = [
                SimpleNamespace(id=101, title="A", url="http://example.com/a", price=100),
                SimpleNamespace(id=202, title="B", url="http://example.com/b", price=200),
            ]
            user_repo.get_by_id.side_effect = [
                SimpleNamespace(id=1, email="user1@example.com"),
                SimpleNamespace(id=2, email="user2@example.com"),
            ]
            email_sender.send_many.side_effect = [RuntimeError("smtp down"), None]

            processed = notification_pipeline.process_pending_deliveries(db, batch_size=10)

        self.assertEqual(processed, 2)
        self.assertEqual(delivery_repo.mark_failed.call_count, 1)
        self.assertEqual(delivery_repo.mark_sent.call_count, 1)
        delivery_repo.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
