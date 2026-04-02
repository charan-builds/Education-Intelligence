from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.domain.services import auth_rules


def test_determine_login_state_reflects_email_mfa_and_profile_flags():
    user = SimpleNamespace(
        is_email_verified=True,
        email_verified_at=None,
        mfa_enabled=True,
        is_profile_completed=False,
    )

    state = auth_rules.determine_login_state(user)

    assert state.email_verified is True
    assert state.mfa_required is True
    assert state.requires_profile_completion is True


def test_lockout_deadline_reached_handles_naive_and_aware_timestamps():
    future = datetime.now(timezone.utc) + timedelta(minutes=5)
    future_naive = future.replace(tzinfo=None)

    assert auth_rules.lockout_deadline_reached(locked_until=future) is True
    assert auth_rules.lockout_deadline_reached(locked_until=future_naive) is True
    assert auth_rules.lockout_deadline_reached(locked_until=None) is False


def test_increment_failed_login_attempts_defaults_cleanly():
    assert auth_rules.increment_failed_login_attempts(None) == 1
    assert auth_rules.increment_failed_login_attempts(4) == 5
