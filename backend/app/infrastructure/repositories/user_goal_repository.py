from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.goal import Goal
from app.domain.models.user_goal import UserGoal
from app.infrastructure.repositories.base_repository import BaseRepository


class UserGoalRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_active_for_user(self, *, user_id: int, tenant_id: int) -> UserGoal | None:
        result = await self.session.execute(
            select(UserGoal)
            .options(selectinload(UserGoal.goal))
            .join(Goal, Goal.id == UserGoal.goal_id)
            .where(UserGoal.user_id == user_id, UserGoal.is_active.is_(True), Goal.tenant_id == tenant_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_link(self, *, user_id: int, goal_id: int) -> UserGoal | None:
        result = await self.session.execute(
            select(UserGoal).where(UserGoal.user_id == user_id, UserGoal.goal_id == goal_id)
        )
        return result.scalar_one_or_none()

    async def deactivate_all_for_user(self, *, user_id: int) -> None:
        await self.session.execute(
            update(UserGoal).where(UserGoal.user_id == user_id, UserGoal.is_active.is_(True)).values(is_active=False)
        )

    async def create_or_activate(self, *, user_id: int, goal_id: int) -> UserGoal:
        link = await self.get_link(user_id=user_id, goal_id=goal_id)
        if link is None:
            link = UserGoal(user_id=user_id, goal_id=goal_id, is_active=True)
            self.session.add(link)
        else:
            link.is_active = True
        await self.session.flush()
        return link
