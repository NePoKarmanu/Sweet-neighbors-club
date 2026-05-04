from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from backend.tasks.notifications import run_full_pipeline_task


class NotificationsTaskTests(unittest.TestCase):
    @patch("backend.tasks.notifications.SessionLocal")
    @patch("backend.tasks.notifications.process_pending_deliveries")
    @patch("backend.tasks.notifications.materialize_pending_deliveries")
    @patch("backend.tasks.notifications.match_listings_to_subscriptions")
    def test_run_full_pipeline_task_returns_aggregated_result(
        self,
        mock_match: MagicMock,
        mock_materialize: MagicMock,
        mock_process: MagicMock,
        mock_session_local: MagicMock,
    ) -> None:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_match.return_value = 7
        mock_materialize.return_value = 5
        mock_process.return_value = 4

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
        mock_db.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
