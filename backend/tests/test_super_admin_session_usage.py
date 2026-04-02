from __future__ import annotations

from pathlib import Path

from app.infrastructure.database import ALLOWED_SUPER_ADMIN_SESSION_REASONS


def test_open_system_session_not_used_in_application_code() -> None:
    allowed_files = {
        Path("backend/app/infrastructure/database.py"),
    }
    offenders: list[str] = []
    for path in Path("backend/app").rglob("*.py"):
        if path in allowed_files:
            continue
        text = path.read_text(encoding="utf-8")
        if "open_system_session(" in text:
            offenders.append(str(path))
    assert offenders == [], f"Use open_super_admin_session() explicitly instead of open_system_session(): {offenders}"


def test_open_super_admin_session_includes_reason_at_callsite() -> None:
    allowed_files = {
        Path("backend/app/infrastructure/database.py"),
    }
    offenders: list[str] = []
    for path in Path("backend/app").rglob("*.py"):
        if path in allowed_files:
            continue
        text = path.read_text(encoding="utf-8")
        if "open_super_admin_session()" in text:
            offenders.append(str(path))
    assert offenders == [], f"Pass an explicit reason to open_super_admin_session(): {offenders}"


def test_open_super_admin_session_reasons_are_whitelisted() -> None:
    expected = {
        "health_check",
        "open_system_session_alias",
        "mark_outbox_processed_without_tenant",
        "mark_outbox_failed_without_tenant",
        "list_student_tenant_ids",
        "process_outbox_events",
        "cleanup_outbox_events",
        "refresh_outbox_metrics",
        "recover_stuck_outbox_events",
        "refresh_platform_overview",
        "consume_kafka_events",
        "replay_kafka_topic",
    }
    assert ALLOWED_SUPER_ADMIN_SESSION_REASONS == expected
