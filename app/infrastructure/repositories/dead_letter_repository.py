from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.dead_letter_event import DeadLetterEvent


class DeadLetterRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_event(
        self,
        *,
        tenant_id: int | None,
        source_event_id: int | None,
        source_type: str,
        event_type: str,
        payload_json: str,
        error_message: str,
        attempts: int,
    ) -> DeadLetterEvent:
        row = DeadLetterEvent(
            tenant_id=tenant_id,
            source_event_id=source_event_id,
            source_type=source_type,
            event_type=event_type,
            payload_json=payload_json,
            error_message=error_message[:512],
            attempts=attempts,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def delete_older_than(self, *, days: int) -> int:
        threshold = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.session.execute(delete(DeadLetterEvent).where(DeadLetterEvent.created_at < threshold))
        return int(result.rowcount or 0)

    async def list_recent(self, *, tenant_id: int | None, limit: int = 100) -> list[DeadLetterEvent]:
        stmt = select(DeadLetterEvent).order_by(DeadLetterEvent.id.desc()).limit(limit)
        if tenant_id is not None:
            stmt = stmt.where(DeadLetterEvent.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
