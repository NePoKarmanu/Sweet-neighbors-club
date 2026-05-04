from __future__ import annotations

import unittest
import sys
from types import SimpleNamespace
import types
from unittest.mock import patch

from fastapi.testclient import TestClient

if "jwt" not in sys.modules:
    jwt_module = types.ModuleType("jwt")
    jwt_module.InvalidTokenError = Exception
    sys.modules["jwt"] = jwt_module

from backend.main import create_app
from backend.utils.auth import get_current_user


class ScrapingApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_staff_can_queue_all_providers(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_staff=True)

        with patch("backend.routers.scraping.run_all_scrapers_task.delay") as mock_delay:
            mock_delay.return_value = SimpleNamespace(id="task-123")
            response = self.client.post("/scraping/run")

        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.json(),
            {"task_id": "task-123", "provider": None, "mode": "all"},
        )
        mock_delay.assert_called_once_with(None)

    def test_staff_can_queue_single_provider(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_staff=True)

        with patch("backend.routers.scraping.run_all_scrapers_task.delay") as mock_delay:
            mock_delay.return_value = SimpleNamespace(id="task-456")
            response = self.client.post("/scraping/run?provider=cian")

        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.json(),
            {"task_id": "task-456", "provider": "cian", "mode": "single"},
        )
        mock_delay.assert_called_once_with("cian")

    def test_non_staff_gets_forbidden(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_staff=False)

        response = self.client.post("/scraping/run")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "forbidden_error")

    def test_unknown_provider_returns_422(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_staff=True)

        response = self.client.post("/scraping/run?provider=unknown_provider")

        self.assertEqual(response.status_code, 422)

    def test_empty_provider_returns_422(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_staff=True)

        response = self.client.post("/scraping/run?provider=   ")

        self.assertEqual(response.status_code, 422)

    def test_unknown_task_id_returns_404(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_staff=True)
        pending_result = SimpleNamespace(state="PENDING", result=None)
        with patch("backend.routers.scraping.AsyncResult", return_value=pending_result):
            response = self.client.get("/scraping/tasks/unknown-task-id")
        self.assertEqual(response.status_code, 404)

    def test_known_task_id_returns_status_payload(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_staff=True)
        done_result = SimpleNamespace(state="SUCCESS", result={"created": 10})
        with patch("backend.routers.scraping.AsyncResult", return_value=done_result):
            response = self.client.get("/scraping/tasks/known-task-id")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"task_id": "known-task-id", "state": "SUCCESS", "result": {"created": 10}},
        )


if __name__ == "__main__":
    unittest.main()
