from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.event_consumer_state import EventConsumerState


class EventConsumerStateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_message(
        self,
        *,
        consumer_name: str,
        message_id: str,
    ) -> EventConsumerState | None:
        return await self.session.scalar(
            select(EventConsumerState).where(
                EventConsumerState.consumer_name == consumer_name,
                EventConsumerState.message_id == message_id,
            )
        )

    async def get_or_create(
        self,
        *,
        consumer_name: str,
        event_name: str,
        message_id: str,
        tenant_id: int | None,
    ) -> EventConsumerState:
        existing = await self.get_by_message(consumer_name=consumer_name, message_id=message_id)
        if existing is not None:
            return existing
        row = EventConsumerState(
            tenant_id=tenant_id,
            consumer_name=consumer_name,
            event_name=event_name,
            message_id=message_id,
            status="pending",
            attempts=0,
            last_error=None,
            first_received_at=datetime.now(timezone.utc),
            last_processed_at=None,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def mark_processing(self, row: EventConsumerState, *, attempts: int) -> None:
        row.status = "processing"
        row.attempts = max(int(attempts), int(row.attempts))
        row.last_error = None

    async def mark_processed(self, row: EventConsumerState, *, attempts: int) -> None:
        row.status = "processed"
        row.attempts = max(int(attempts), int(row.attempts))
        row.last_error = None
        row.last_processed_at = datetime.now(timezone.utc)

    async def mark_failed(
        self,
        row: EventConsumerState,
        *,
        attempts: int,
        error_message: str,
        dead: bool,
    ) -> None:
        row.status = "dead" if dead else "failed"
        row.attempts = max(int(attempts), int(row.attempts))
        row.last_error = error_message[:512]
        row.last_processed_at = datetime.now(timezone.utc)
