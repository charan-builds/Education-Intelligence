from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.learning_profile import LearningProfile
from app.domain.models.user import User
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.tenant_scoping import user_belongs_to_tenant


class LearningProfileRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_for_user(self, *, user_id: int, tenant_id: int) -> LearningProfile | None:
        result = await self.session.execute(
            select(LearningProfile)
            .join(User, User.id == LearningProfile.user_id)
            .where(
                LearningProfile.user_id == user_id,
                user_belongs_to_tenant(User, tenant_id),
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_for_user(self, *, user_id: int, tenant_id: int) -> LearningProfile:
        existing = await self.get_for_user(user_id=user_id, tenant_id=tenant_id)
        if existing is not None:
            return existing
        profile = LearningProfile(user_id=user_id)
        self.session.add(profile)
        await self.session.flush()
        return profile
