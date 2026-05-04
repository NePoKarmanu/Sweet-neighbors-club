from __future__ import annotations

import unittest
import sys
from types import SimpleNamespace
import types
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

if "jwt" not in sys.modules:
    jwt_module = types.ModuleType("jwt")
    jwt_module.InvalidTokenError = Exception
    sys.modules["jwt"] = jwt_module

if "pywebpush" not in sys.modules:
    pywebpush_module = types.ModuleType("pywebpush")
    pywebpush_module.WebPushException = Exception
    pywebpush_module.webpush = lambda *args, **kwargs: None
    sys.modules["pywebpush"] = pywebpush_module

from backend.db.session import get_db
from backend.main import create_app
from backend.utils.auth import get_current_user


class NotificationsApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.client = TestClient(self.app)
        self.app.dependency_overrides[get_db] = lambda: iter([MagicMock()])

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_post_notifications_requires_auth(self) -> None:
        payload = {
            "city": "Voronezh",
            "notify_email": True,
            "notify_push": False,
        }
        response = self.client.post("/notifications", json=payload)
        self.assertEqual(response.status_code, 401)

    def test_post_notifications_creates_settings(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, email="u@x.com")
        payload = {
            "city": "Voronezh",
            "notify_email": True,
            "notify_push": False,
        }
        with patch("backend.routers.notifications.create_notification_settings") as mock_create:
            mock_create.return_value = {
                "subscription_id": 1,
                "filter_id": 1,
                "notify_email": True,
                "notify_push": False,
                "is_active": True,
            }
            response = self.client.post("/notifications", json=payload)
        self.assertEqual(response.status_code, 201)

    def test_post_notifications_rejects_disabled_channels(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, email="u@x.com")
        payload = {
            "city": "Voronezh",
            "notify_email": False,
            "notify_push": False,
        }
        response = self.client.post("/notifications", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_post_notifications_rejects_invalid_creator_types_with_422(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, email="u@x.com")
        payload = {
            "city": "voronezh",
            "notify_email": True,
            "notify_push": False,
            "creator_types": ["string"],
        }
        with patch("backend.routers.notifications.create_notification_settings") as mock_create:
            mock_create.return_value = {
                "subscription_id": 1,
                "filter_id": 1,
                "notify_email": True,
                "notify_push": False,
                "is_active": True,
            }
            response = self.client.post("/notifications", json=payload)
        self.assertEqual(response.status_code, 201)

    def test_post_notifications_accepts_valid_creator_types(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, email="u@x.com")
        payload = {
            "city": "voronezh",
            "notify_email": True,
            "notify_push": False,
            "creator_types": ["agency"],
        }
        with patch("backend.routers.notifications.create_notification_settings") as mock_create:
            mock_create.return_value = {
                "subscription_id": 1,
                "filter_id": 1,
                "notify_email": True,
                "notify_push": False,
                "is_active": True,
            }
            response = self.client.post("/notifications", json=payload)
        self.assertEqual(response.status_code, 201)

    def test_staff_can_queue_notifications_pipeline(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_staff=True)

        with patch("backend.routers.notifications.run_full_pipeline_task.delay") as mock_delay:
            mock_delay.return_value = SimpleNamespace(id="notif-task-1")
            response = self.client.post("/notifications/admin/run")

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), {"task_id": "notif-task-1", "mode": "full", "user_id": None})
        mock_delay.assert_called_once_with(None)

    def test_staff_can_queue_notifications_pipeline_for_specific_user(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_staff=True)

        with patch("backend.routers.notifications.run_full_pipeline_task.delay") as mock_delay:
            mock_delay.return_value = SimpleNamespace(id="notif-task-2")
            response = self.client.post("/notifications/admin/run?user_id=42")

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), {"task_id": "notif-task-2", "mode": "full", "user_id": 42})
        mock_delay.assert_called_once_with(42)

    def test_non_staff_cannot_queue_notifications_pipeline(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_staff=False)

        response = self.client.post("/notifications/admin/run")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "forbidden_error")

    def test_known_notifications_task_id_returns_status_payload(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_staff=True)
        done_result = SimpleNamespace(
            state="SUCCESS",
            result={
                "created_notifications": 3,
                "created_deliveries": 2,
                "processed_deliveries": 2,
                "user_id": 42,
            },
        )
        with patch("backend.routers.notifications.AsyncResult", return_value=done_result):
            response = self.client.get("/notifications/admin/tasks/task-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "task_id": "task-1",
                "state": "SUCCESS",
                "result": {
                    "created_notifications": 3,
                    "created_deliveries": 2,
                    "processed_deliveries": 2,
                    "user_id": 42,
                },
            },
        )

    def test_unknown_notifications_task_id_returns_404(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_staff=True)
        pending_result = SimpleNamespace(state="PENDING", result=None)
        with patch("backend.routers.notifications.AsyncResult", return_value=pending_result):
            response = self.client.get("/notifications/admin/tasks/unknown")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
