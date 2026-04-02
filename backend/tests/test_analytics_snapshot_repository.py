from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from sqlalchemy.exc import IntegrityError

from app.infrastructure.repositories.analytics_snapshot_repository import AnalyticsSnapshotRepository


class _FakeResult:
    pass


class _FakeSession:
    def __init__(self, *, dialect_name: str) -> None:
        self.bind = SimpleNamespace(dialect=SimpleNamespace(name=dialect_name))
        self.executed: list[tuple[object, dict | None]] = []
        self.scalar_value = 7
        self.added = []
        self.flushed = False
        self.flush_failures_remaining = 0

    async def execute(self, statement, params=None):
        self.executed.append((statement, params))
        return _FakeResult()

    async def scalar(self, statement):
        self.executed.append((statement, None))
        return self.scalar_value

    def add(self, row) -> None:
        self.added.append(row)

    async def flush(self) -> None:
        if self.flush_failures_remaining > 0:
            self.flush_failures_remaining -= 1
            raise IntegrityError("insert", {}, Exception("duplicate key"))
        self.flushed = True

    def begin_nested(self):
        class _Nested:
            async def __aenter__(self_nonlocal):
                return self_nonlocal

            async def __aexit__(self_nonlocal, exc_type, exc, tb):
                return False

        return _Nested()


async def test_create_snapshot_version_uses_postgres_advisory_lock():
    session = _FakeSession(dialect_name="postgresql")
    repo = AnalyticsSnapshotRepository(session)

    row = await repo.create_snapshot_version(
        tenant_id=3,
        snapshot_type="user_learning_summary",
        subject_id=9,
        payload_json="{}",
        window_start=datetime.now(timezone.utc),
        window_end=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    first_statement, first_params = session.executed[0]
    assert "pg_advisory_xact_lock" in str(first_statement)
    assert first_params == {
        "namespace": "analytics_snapshots",
        "lock_key": "analytics_snapshot:3:user_learning_summary:9",
    }
    assert row.snapshot_version == 8
    assert session.flushed is True


async def test_create_snapshot_version_skips_advisory_lock_outside_postgres():
    session = _FakeSession(dialect_name="sqlite")
    repo = AnalyticsSnapshotRepository(session)

    row = await repo.create_snapshot_version(
        tenant_id=None,
        snapshot_type="platform_overview",
        subject_id=None,
        payload_json="{}",
        window_start=datetime.now(timezone.utc),
        window_end=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    first_statement, _ = session.executed[0]
    assert "pg_advisory_xact_lock" not in str(first_statement)
    assert row.snapshot_version == 8


async def test_create_snapshot_version_retries_once_on_integrity_error():
    session = _FakeSession(dialect_name="postgresql")
    session.flush_failures_remaining = 1
    repo = AnalyticsSnapshotRepository(session)

    row = await repo.create_snapshot_version(
        tenant_id=3,
        snapshot_type="user_learning_summary",
        subject_id=9,
        payload_json="{}",
        window_start=datetime.now(timezone.utc),
        window_end=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert row.snapshot_version == 8
    advisory_lock_calls = [statement for statement, _ in session.executed if "pg_advisory_xact_lock" in str(statement)]
    assert len(advisory_lock_calls) == 2
    assert session.flushed is True
