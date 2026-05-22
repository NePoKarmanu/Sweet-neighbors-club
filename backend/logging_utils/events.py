from __future__ import annotations

import logging
from typing import Any


def _build_extra(event: str, **context: Any) -> dict[str, Any]:
    extra: dict[str, Any] = {"event": event}
    extra.update(context)
    return extra


def log_info(logger: logging.Logger, message: str, *, event: str, **context: Any) -> None:
    logger.info(message, extra=_build_extra(event, **context))


def log_warning(logger: logging.Logger, message: str, *, event: str, **context: Any) -> None:
    logger.warning(message, extra=_build_extra(event, **context))


def log_error(logger: logging.Logger, message: str, *, event: str, **context: Any) -> None:
    logger.error(message, extra=_build_extra(event, **context))


def log_exception(logger: logging.Logger, message: str, *, event: str, **context: Any) -> None:
    logger.exception(message, extra=_build_extra(event, **context))
