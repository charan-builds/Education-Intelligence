from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.gamification_profile import GamificationProfile
from app.infrastructure.repositories.base_repository import BaseRepository


class GamificationProfileRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_for_user(self, *, tenant_id: int, user_id: int, for_update: bool = False) -> GamificationProfile | None:
        stmt = select(GamificationProfile).where(
            GamificationProfile.tenant_id == tenant_id,
            GamificationProfile.user_id == user_id,
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, *, tenant_id: int, user_id: int, for_update: bool = False) -> GamificationProfile:
        profile = await self.get_for_user(tenant_id=tenant_id, user_id=user_id, for_update=for_update)
        if profile is not None:
            return profile
        now = datetime.now(timezone.utc)
        profile = GamificationProfile(
            tenant_id=tenant_id,
            user_id=user_id,
            level=1,
            total_xp=0,
            current_level_xp=0,
            xp_to_next_level=200,
            current_streak_days=0,
            longest_streak_days=0,
            completed_topics_count=0,
            completed_tests_count=0,
            created_at=now,
            updated_at=now,
        )
        self.session.add(profile)
        await self.session.flush()
        return profile
