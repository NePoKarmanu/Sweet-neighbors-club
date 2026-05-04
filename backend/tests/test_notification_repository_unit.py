from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from backend.db.repositories.notification_deliveries import NotificationDeliveryRepository
from backend.db.repositories.notifications import NotificationRepository


class NotificationRepositoryUnitTests(unittest.TestCase):
    def test_create_if_missing_concurrent_attempts_create_only_once(self) -> None:
        session = MagicMock()
        repository = NotificationRepository(session)

        created_notification = MagicMock()
        session.scalar.side_effect = [101, None]
        repository.get_by_id = MagicMock(return_value=created_notification)

        first_result = repository.create_if_missing(user_id=7, listing_id=21)
        second_result = repository.create_if_missing(user_id=7, listing_id=21)

        self.assertIs(first_result, created_notification)
        self.assertIsNone(second_result)
        self.assertEqual(session.scalar.call_count, 2)
        repository.get_by_id.assert_called_once_with(101)


class NotificationDeliveryRepositoryUnitTests(unittest.TestCase):
    def test_materialize_channels_concurrent_attempts_create_only_missing_rows(self) -> None:
        session = MagicMock()
        repository = NotificationDeliveryRepository(session)

        session.scalars.side_effect = [iter([11, 12]), iter([])]

        first_created = repository.materialize_channels_for_notification(
            notification_id=55,
            include_email=True,
            include_push=True,
        )
        second_created = repository.materialize_channels_for_notification(
            notification_id=55,
            include_email=True,
            include_push=True,
        )

        self.assertEqual(first_created, 2)
        self.assertEqual(second_created, 0)
        self.assertEqual(session.scalars.call_count, 2)


if __name__ == "__main__":
    unittest.main()
