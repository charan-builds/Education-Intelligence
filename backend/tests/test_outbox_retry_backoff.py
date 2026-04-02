import asyncio
from datetime import datetime, timezone

from app.domain.models.outbox_event import OutboxEvent
from app.infrastructure.repositories.outbox_repository import OutboxRepository


class _Session:
    async def execute(self, _stmt):
        raise AssertionError("No SQL expected in this unit test")


def test_outbox_retry_uses_exponential_backoff():
    async def _run():
        repository = OutboxRepository(_Session())  # type: ignore[arg-type]
        event = OutboxEvent(
            tenant_id=1,
            event_type="celery_task",
            payload_json="{}",
            status="queued",
            attempts=0,
            error_message=None,
            created_at=datetime.now(timezone.utc),
            available_at=datetime.now(timezone.utc),
            dispatched_at=None,
            processed_at=None,
        )

        await repository.mark_failed(event, "first failure", retry_delay_seconds=10, max_attempts=5)
        first_delay = (event.available_at - datetime.now(timezone.utc)).total_seconds()
        assert event.status == "failed"
        assert 8 <= first_delay <= 12

        await repository.mark_failed(event, "second failure", retry_delay_seconds=10, max_attempts=5)
        second_delay = (event.available_at - datetime.now(timezone.utc)).total_seconds()
        assert 18 <= second_delay <= 22

    asyncio.run(_run())
