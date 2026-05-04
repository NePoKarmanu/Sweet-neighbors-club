from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppError(Exception):
    detail: Any
    code: str = "app_error"
    status_code: int = 400
    meta: dict[str, Any] = field(default_factory=dict)


class ValidationAppError(AppError):
    def __init__(self, detail: Any, *, meta: dict[str, Any] | None = None) -> None:
        super().__init__(
            detail=detail,
            code="validation_error",
            status_code=422,
            meta=meta or {},
        )


class AuthAppError(AppError):
    def __init__(self, detail: Any = "Unauthorized", *, meta: dict[str, Any] | None = None) -> None:
        super().__init__(
            detail=detail,
            code="auth_error",
            status_code=401,
            meta=meta or {},
        )


class ForbiddenAppError(AppError):
    def __init__(self, detail: Any = "Forbidden", *, meta: dict[str, Any] | None = None) -> None:
        super().__init__(
            detail=detail,
            code="forbidden_error",
            status_code=403,
            meta=meta or {},
        )


class NotFoundAppError(AppError):
    def __init__(self, detail: Any = "Not found", *, meta: dict[str, Any] | None = None) -> None:
        super().__init__(
            detail=detail,
            code="not_found_error",
            status_code=404,
            meta=meta or {},
        )


class ConflictAppError(AppError):
    def __init__(self, detail: Any, *, meta: dict[str, Any] | None = None) -> None:
        super().__init__(
            detail=detail,
            code="conflict_error",
            status_code=409,
            meta=meta or {},
        )


class ExternalServiceAppError(AppError):
    def __init__(self, detail: Any, *, meta: dict[str, Any] | None = None) -> None:
        super().__init__(
            detail=detail,
            code="external_service_error",
            status_code=503,
            meta=meta or {},
        )
