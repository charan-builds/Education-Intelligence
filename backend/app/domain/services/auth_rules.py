from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class LoginState:
    email_verified: bool
    mfa_required: bool
    requires_profile_completion: bool


def is_email_verified(user: object) -> bool:
    return bool(getattr(user, "is_email_verified", False) or getattr(user, "email_verified_at", None))


def is_mfa_enabled(user: object) -> bool:
    return bool(getattr(user, "mfa_enabled", False))


def requires_profile_completion(user: object) -> bool:
    return not bool(getattr(user, "is_profile_completed", False))


def lockout_deadline_reached(*, locked_until: datetime | None, now: datetime | None = None) -> bool:
    if locked_until is None:
        return False
    current_time = now or datetime.now(timezone.utc)
    normalized = locked_until if locked_until.tzinfo is not None else locked_until.replace(tzinfo=timezone.utc)
    return normalized > current_time


def increment_failed_login_attempts(current_attempts: int | None) -> int:
    return int(current_attempts or 0) + 1


def determine_login_state(user: object) -> LoginState:
    return LoginState(
        email_verified=is_email_verified(user),
        mfa_required=is_mfa_enabled(user),
        requires_profile_completion=requires_profile_completion(user),
    )
