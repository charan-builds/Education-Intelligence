from datetime import datetime, timezone
from types import SimpleNamespace

from app.domain.models.outbox_event import OutboxEvent
from app.infrastructure.repositories.outbox_repository import OutboxRepository


async def _noop(*args, **kwargs):
    return None


class _SessionStub:
    async def execute(self, *args, **kwargs):  # pragma: no cover
        return None


def _event(attempts: int = 0) -> OutboxEvent:
    now = datetime.now(timezone.utc)
    return OutboxEvent(
        id=1,
        tenant_id=1,
        event_type="celery_task",
        payload_json="{}",
        status="pending",
        attempts=attempts,
        error_message=None,
        created_at=now,
        available_at=now,
        dispatched_at=None,
    )


import asyncio


def test_mark_failed_sets_dead_when_attempt_limit_reached():
    async def _run():
        repo = OutboxRepository(_SessionStub())  # type: ignore[arg-type]
        event = _event(attempts=4)

        await repo.mark_failed(event, "queue down", retry_delay_seconds=60, max_attempts=5)

        assert event.attempts == 5
        assert event.status == "dead"
        assert event.error_message == "queue down"

    asyncio.run(_run())


def test_mark_failed_keeps_pending_before_limit():
    async def _run():
        repo = OutboxRepository(_SessionStub())  # type: ignore[arg-type]
        event = _event(attempts=1)
        original_available_at = event.available_at

        await repo.mark_failed(event, "temporary failure", retry_delay_seconds=60, max_attempts=5)

        assert event.attempts == 2
        assert event.status == "pending"
        assert event.error_message == "temporary failure"
        assert event.available_at >= original_available_at

    asyncio.run(_run())


def test_create_event_includes_tenant_for_idempotency_key():
    class _SessionCapture:
        def __init__(self):
            self.last_stmt = None

        async def execute(self, stmt, *args, **kwargs):
            self.last_stmt = str(stmt)
            return SimpleNamespace(scalar_one_or_none=lambda: None)

        def add(self, row):
            self.row = row

        async def flush(self):
            return None

    async def _run():
        session = _SessionCapture()
        repo = OutboxRepository(session)
        await repo.create_event(
            tenant_id=99,
            event_type="test_event",
            payload_json='{"a":1}',
            idempotency_key="key-99",
        )
        assert "tenant_id" in session.last_stmt
        assert "idempotency_key" in session.last_stmt

    asyncio.run(_run())


def test_create_event_without_idempotency_uses_payload_and_tenant():
    class _SessionCapture:
        def __init__(self):
            self.last_stmt = None

        async def execute(self, stmt, *args, **kwargs):
            self.last_stmt = str(stmt)
            return SimpleNamespace(scalar_one_or_none=lambda: None)

        def add(self, row):
            self.row = row

        async def flush(self):
            return None

    async def _run():
        session = _SessionCapture()
        repo = OutboxRepository(session)
        await repo.create_event(
            tenant_id=101,
            event_type="test_event",
            payload_json='{"a":1}',
            idempotency_key=None,
        )
        assert "tenant_id" in session.last_stmt
        assert "payload_json" in session.last_stmt

    asyncio.run(_run())
