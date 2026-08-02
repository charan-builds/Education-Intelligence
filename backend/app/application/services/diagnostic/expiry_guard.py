from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone

from app.application.exceptions import ValidationError


DEFAULT_TEST_DURATION_MINUTES = 20


def diagnostic_expires_at(test: object) -> datetime:
    started_at = _as_utc(getattr(test, "started_at"))
    duration_minutes = _duration_minutes(test)
    return started_at + timedelta(minutes=duration_minutes)


async def enforce_diagnostic_not_expired(
    test: object,
    *,
    diagnostic_repository: object,
    commit: Callable[[], Awaitable[object]] | None = None,
    now: datetime | None = None,
) -> None:
    if getattr(test, "expired_at", None) is not None:
        raise ValidationError("Diagnostic test expired")

    current_time = now or datetime.now(timezone.utc)
    if current_time <= diagnostic_expires_at(test):
        return

    await _mark_expired(test, diagnostic_repository=diagnostic_repository, expired_at=current_time)
    if commit is not None:
        await commit()
    raise ValidationError("Diagnostic test expired")


async def _mark_expired(test: object, *, diagnostic_repository: object, expired_at: datetime) -> None:
    expire_test = getattr(diagnostic_repository, "expire_test", None)
    if expire_test is not None:
        result = expire_test(test, expired_at)
        if inspect.isawaitable(result):
            await result
        return

    setattr(test, "status", "expired")
    setattr(test, "expired_at", expired_at)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _duration_minutes(test: object) -> int:
    try:
        duration = int(getattr(test, "test_duration", DEFAULT_TEST_DURATION_MINUTES) or DEFAULT_TEST_DURATION_MINUTES)
    except (TypeError, ValueError):
        duration = DEFAULT_TEST_DURATION_MINUTES
    return max(1, duration)
