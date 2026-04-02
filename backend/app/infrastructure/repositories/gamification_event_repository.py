import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.gamification_event import GamificationEvent
from app.infrastructure.repositories.base_repository import BaseRepository


class GamificationEventRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_idempotency_key(self, *, tenant_id: int, user_id: int, idempotency_key: str) -> GamificationEvent | None:
        result = await self.session.execute(
            select(GamificationEvent).where(
                GamificationEvent.tenant_id == tenant_id,
                GamificationEvent.user_id == user_id,
                GamificationEvent.idempotency_key == idempotency_key,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        tenant_id: int,
        user_id: int,
        event_type: str,
        source_type: str,
        source_id: int,
        xp_delta: int,
        level_after: int,
        streak_after: int,
        idempotency_key: str,
        topic_id: int | None = None,
        diagnostic_test_id: int | None = None,
        metadata: dict | None = None,
        awarded_at: datetime | None = None,
    ) -> GamificationEvent:
        event_time = awarded_at or datetime.now(timezone.utc)
        row = GamificationEvent(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            source_type=source_type,
            source_id=source_id,
            topic_id=topic_id,
            diagnostic_test_id=diagnostic_test_id,
            xp_delta=xp_delta,
            level_after=level_after,
            streak_after=streak_after,
            metadata_json=json.dumps(metadata or {}, default=str),
            idempotency_key=idempotency_key,
            awarded_at=event_time,
            created_at=event_time,
        )
        self.session.add(row)
        await self.session.flush()
        return row
