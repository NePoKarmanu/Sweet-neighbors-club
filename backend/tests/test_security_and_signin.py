from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.dto.auth import SigninDTO
from backend.services.signin import signin_user
from backend.utils.security import hash_password, verify_password


def test_verify_new_hash_success() -> None:
    password = "SuperSecret123"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash)


def test_verify_new_hash_wrong_password() -> None:
    password_hash = hash_password("CorrectPassword123")

    assert not verify_password("WrongPassword123", password_hash)


def test_signin_success_with_new_hash() -> None:
    password = "Password123!"
    user = SimpleNamespace(
        id=1,
        email="user@example.com",
        phone="+15551234567",
        is_staff=False,
        password_hash=hash_password(password),
    )

    db = MagicMock()
    users_repo = MagicMock()
    users_repo.get_by_email.return_value = user

    data = SigninDTO(email=user.email, password=password)

    from backend.services import signin as signin_module

    original_repo = signin_module.UserRepository
    original_token_creator = signin_module.create_access_token
    signin_module.UserRepository = MagicMock(return_value=users_repo)
    signin_module.create_access_token = MagicMock(return_value="token")

    try:
        response = signin_user(data, db)
    finally:
        signin_module.UserRepository = original_repo
        signin_module.create_access_token = original_token_creator

    assert response.access_token == "token"
    assert response.user.id == user.id


def test_signin_fail_with_wrong_password() -> None:
    user = SimpleNamespace(
        id=1,
        email="user@example.com",
        phone="+15551234567",
        is_staff=False,
        password_hash=hash_password("Password123!"),
    )

    db = MagicMock()
    users_repo = MagicMock()
    users_repo.get_by_email.return_value = user

    data = SigninDTO(email=user.email, password="WrongPassword123!")

    from backend.exceptions import AuthAppError
    from backend.services import signin as signin_module

    original_repo = signin_module.UserRepository
    signin_module.UserRepository = MagicMock(return_value=users_repo)

    try:
        try:
            signin_user(data, db)
            assert False, "Expected AuthAppError"
        except AuthAppError:
            pass
    finally:
        signin_module.UserRepository = original_repo
