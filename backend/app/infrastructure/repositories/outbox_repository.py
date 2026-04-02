from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.outbox_event import OutboxEvent


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_event(
        self,
        *,
        tenant_id: int | None,
        event_type: str,
        payload_json: str,
        idempotency_key: str | None = None,
    ) -> OutboxEvent:
        now = datetime.now(timezone.utc)
        stmt = select(OutboxEvent).where(OutboxEvent.event_type == event_type)
        if idempotency_key is not None:
            stmt = stmt.where(
                OutboxEvent.idempotency_key == idempotency_key,
                OutboxEvent.tenant_id == tenant_id,
            )
        else:
            stmt = stmt.where(
                OutboxEvent.tenant_id == tenant_id,
                OutboxEvent.payload_json == payload_json,
            )
        stmt = stmt.order_by(OutboxEvent.id.desc()).limit(1)
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            return existing
        row = OutboxEvent(
            tenant_id=tenant_id,
            event_type=event_type,
            idempotency_key=idempotency_key,
            payload_json=payload_json,
            status="queued",
            attempts=0,
            error_message=None,
            created_at=now,
            available_at=now,
            dispatched_at=None,
            processed_at=None,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_ready(self, limit: int = 100) -> list[OutboxEvent]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(OutboxEvent)
            .where(and_(OutboxEvent.status.in_(("queued", "failed")), OutboxEvent.available_at <= now))
            .order_by(OutboxEvent.id.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_pending(self, limit: int = 100) -> list[OutboxEvent]:
        return await self.list_ready(limit=limit)

    async def list_by_status(
        self,
        *,
        status: str,
        tenant_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[OutboxEvent]:
        stmt = select(OutboxEvent).where(OutboxEvent.status == status)
        if tenant_id is not None:
            stmt = stmt.where(OutboxEvent.tenant_id == tenant_id)
        stmt = stmt.order_by(OutboxEvent.id.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_status(self, *, status: str, tenant_id: int | None = None) -> int:
        stmt = select(func.count(OutboxEvent.id)).where(OutboxEvent.status == status)
        if tenant_id is not None:
            stmt = stmt.where(OutboxEvent.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def mark_dispatched(self, event: OutboxEvent) -> None:
        event.status = "dispatched"
        event.dispatched_at = datetime.now(timezone.utc)
        event.error_message = None
        event.processed_at = None

    async def mark_dispatch_failed(
        self,
        event: OutboxEvent,
        error_message: str,
        retry_delay_seconds: int = 60,
        max_attempts: int = 5,
    ) -> None:
        now = datetime.now(timezone.utc)
        event.attempts = int(event.attempts) + 1
        event.error_message = error_message[:512]
        if int(event.attempts) >= max_attempts:
            event.status = "dead"
            event.available_at = now.replace(microsecond=0)
            return
        exponential_delay = retry_delay_seconds * (2 ** max(event.attempts - 1, 0))
        event.status = "failed"
        event.available_at = (now + timedelta(seconds=exponential_delay)).replace(microsecond=0)

    async def mark_failed(
        self,
        event: OutboxEvent,
        error_message: str,
        retry_delay_seconds: int = 60,
        max_attempts: int = 5,
    ) -> None:
        await self.mark_dispatch_failed(
            event,
            error_message,
            retry_delay_seconds=retry_delay_seconds,
            max_attempts=max_attempts,
        )

    async def mark_processed(self, event: OutboxEvent) -> None:
        event.status = "processed"
        event.error_message = None
        event.processed_at = datetime.now(timezone.utc)

    async def mark_consumption_failed(self, event: OutboxEvent, *, error_message: str, dead: bool = False) -> None:
        event.status = "dead" if dead else "failed"
        event.error_message = error_message[:512]
        event.processed_at = datetime.now(timezone.utc)

    async def get_by_idempotency_key(self, *, tenant_id: int | None, event_type: str, idempotency_key: str) -> OutboxEvent | None:
        result = await self.session.execute(
            select(OutboxEvent).where(
                OutboxEvent.tenant_id == tenant_id,
                OutboxEvent.event_type == event_type,
                OutboxEvent.idempotency_key == idempotency_key,
            )
            .order_by(OutboxEvent.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def mark_processed_by_idempotency_key(self, *, tenant_id: int | None, event_type: str, idempotency_key: str) -> bool:
        row = await self.get_by_idempotency_key(tenant_id=tenant_id, event_type=event_type, idempotency_key=idempotency_key)
        if row is None:
            return False
        await self.mark_processed(row)
        return True

    async def mark_consumption_failed_by_idempotency_key(
        self,
        *,
        tenant_id: int | None,
        event_type: str,
        idempotency_key: str,
        error_message: str,
        dead: bool = False,
    ) -> bool:
        row = await self.get_by_idempotency_key(tenant_id=tenant_id, event_type=event_type, idempotency_key=idempotency_key)
        if row is None:
            return False
        await self.mark_consumption_failed(row, error_message=error_message, dead=dead)
        return True

    async def delete_processed_older_than(self, days: int) -> int:
        threshold = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = delete(OutboxEvent).where(
            and_(OutboxEvent.status == "processed", OutboxEvent.processed_at.is_not(None), OutboxEvent.processed_at < threshold)
        )
        result = await self.session.execute(stmt)
        return int(result.rowcount or 0)

    async def delete_dead_older_than(self, days: int) -> int:
        threshold = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = delete(OutboxEvent).where(and_(OutboxEvent.status == "dead", OutboxEvent.created_at < threshold))
        result = await self.session.execute(stmt)
        return int(result.rowcount or 0)

    async def requeue_dead_events(self, *, tenant_id: int | None, limit: int = 100) -> int:
        base = (
            select(OutboxEvent)
            .where(OutboxEvent.status == "dead")
            .order_by(OutboxEvent.id.asc())
            .limit(limit)
        )
        if tenant_id is not None:
            base = base.where(OutboxEvent.tenant_id == tenant_id)

        result = await self.session.execute(base)
        rows = list(result.scalars().all())
        now = datetime.now(timezone.utc).replace(microsecond=0)
        for row in rows:
            row.status = "queued"
            row.error_message = None
            row.available_at = now
            row.processed_at = None
        return len(rows)

    async def get_by_id(self, event_id: int) -> OutboxEvent | None:
        stmt = select(OutboxEvent).where(OutboxEvent.id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def requeue_dead_event_by_id(self, *, event_id: int, tenant_id: int | None) -> bool:
        row = await self.get_by_id(event_id)
        if row is None:
            return False
        if row.status != "dead":
            return False
        if tenant_id is not None and row.tenant_id != tenant_id:
            return False
        row.status = "queued"
        row.error_message = None
        row.available_at = datetime.now(timezone.utc).replace(microsecond=0)
        row.processed_at = None
        return True

    async def recover_stuck_processing_events(self, *, timeout_seconds: int, limit: int = 500) -> int:
        threshold = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)
        stmt = (
            select(OutboxEvent)
            .where(and_(OutboxEvent.status == "dispatched", OutboxEvent.dispatched_at <= threshold))
            .order_by(OutboxEvent.id.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        now = datetime.now(timezone.utc).replace(microsecond=0)
        for row in rows:
            row.status = "failed"
            row.error_message = "Recovered from stuck dispatched state"
            row.available_at = now
        return len(rows)
