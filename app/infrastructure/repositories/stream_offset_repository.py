from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.processed_stream_event import ProcessedStreamEvent
from app.domain.models.stream_consumer_offset import StreamConsumerOffset


class StreamOffsetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_processed_message(
        self,
        *,
        consumer_group: str,
        topic: str,
        partition: int,
        offset: int,
        message_id: str,
        event_name: str,
        tenant_id: int | None,
    ) -> ProcessedStreamEvent:
        row = ProcessedStreamEvent(
            consumer_group=consumer_group,
            topic=topic,
            partition=partition,
            offset=offset,
            message_id=message_id,
            event_name=event_name,
            tenant_id=tenant_id,
            processed_at=datetime.now(timezone.utc),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def has_processed(self, *, consumer_group: str, message_id: str) -> bool:
        row = await self.session.scalar(
            select(ProcessedStreamEvent).where(
                ProcessedStreamEvent.consumer_group == consumer_group,
                ProcessedStreamEvent.message_id == message_id,
            )
        )
        return row is not None

    async def upsert_offset(self, *, consumer_group: str, topic: str, partition: int, offset: int) -> StreamConsumerOffset:
        row = await self.session.scalar(
            select(StreamConsumerOffset).where(
                StreamConsumerOffset.consumer_group == consumer_group,
                StreamConsumerOffset.topic == topic,
                StreamConsumerOffset.partition == partition,
            )
        )
        if row is None:
            row = StreamConsumerOffset(
                consumer_group=consumer_group,
                topic=topic,
                partition=partition,
                offset=offset,
                updated_at=datetime.now(timezone.utc),
            )
            self.session.add(row)
        else:
            row.offset = offset
            row.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return row
