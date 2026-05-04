from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.utils import jwt as jwt_utils


class JwtSecurityWarningTests(unittest.TestCase):
    def test_warns_for_short_hs256_secret(self) -> None:
        with (
            patch.object(jwt_utils, "JWT_ALGORITHM", "HS256"),
            patch.object(jwt_utils, "JWT_SECRET", "short-secret"),
            self.assertLogs("backend.utils.jwt", level="WARNING") as logs,
        ):
            jwt_utils.warn_if_weak_jwt_secret()
        self.assertTrue(any("at least 32 bytes is recommended" in message for message in logs.output))

    def test_no_warning_for_long_hs256_secret(self) -> None:
        with (
            patch.object(jwt_utils, "JWT_ALGORITHM", "HS256"),
            patch.object(jwt_utils, "JWT_SECRET", "x" * 40),
            patch.object(jwt_utils.logger, "warning") as warning_mock,
        ):
            jwt_utils.warn_if_weak_jwt_secret()
        warning_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
