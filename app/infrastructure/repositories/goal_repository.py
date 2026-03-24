from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.goal import Goal
from app.domain.models.goal_topic import GoalTopic
from app.infrastructure.repositories.base_repository import BaseRepository


class GoalRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_all(self, tenant_id: int, limit: int, offset: int, cursor_id: int | None = None) -> list[Goal]:
        stmt = select(Goal).where(Goal.tenant_id == tenant_id).order_by(Goal.id.asc())
        if cursor_id is not None:
            stmt = stmt.where(Goal.id > cursor_id).limit(limit)
        else:
            stmt = self.apply_pagination(stmt, limit=limit, offset=offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self, tenant_id: int) -> int:
        result = await self.session.execute(select(func.count(Goal.id)).where(Goal.tenant_id == tenant_id))
        return int(result.scalar_one())

    async def get_by_id(self, tenant_id: int, goal_id: int) -> Goal | None:
        result = await self.session.execute(select(Goal).where(Goal.tenant_id == tenant_id, Goal.id == goal_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, tenant_id: int, name: str) -> Goal | None:
        result = await self.session.execute(select(Goal).where(Goal.tenant_id == tenant_id, Goal.name == name))
        return result.scalar_one_or_none()

    async def create_goal(self, tenant_id: int, name: str, description: str) -> Goal:
        goal = Goal(tenant_id=tenant_id, name=name, description=description)
        self.session.add(goal)
        await self.session.flush()
        return goal

    async def update_goal(self, goal: Goal, **updates) -> Goal:
        for field, value in updates.items():
            setattr(goal, field, value)
        await self.session.flush()
        return goal

    async def delete_goal(self, goal: Goal) -> None:
        await self.session.delete(goal)

    async def list_topic_links(self, tenant_id: int, goal_id: int | None = None) -> list[GoalTopic]:
        stmt = (
            select(GoalTopic)
            .join(Goal, Goal.id == GoalTopic.goal_id)
            .where(Goal.tenant_id == tenant_id)
            .order_by(GoalTopic.goal_id.asc(), GoalTopic.topic_id.asc())
        )
        if goal_id is not None:
            stmt = stmt.where(GoalTopic.goal_id == goal_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_topic_link(self, tenant_id: int, goal_id: int, topic_id: int) -> GoalTopic | None:
        result = await self.session.execute(
            select(GoalTopic)
            .join(Goal, Goal.id == GoalTopic.goal_id)
            .where(Goal.tenant_id == tenant_id, GoalTopic.goal_id == goal_id, GoalTopic.topic_id == topic_id)
        )
        return result.scalar_one_or_none()

    async def get_topic_link_by_id(self, tenant_id: int, link_id: int) -> GoalTopic | None:
        result = await self.session.execute(
            select(GoalTopic).join(Goal, Goal.id == GoalTopic.goal_id).where(Goal.tenant_id == tenant_id, GoalTopic.id == link_id)
        )
        return result.scalar_one_or_none()

    async def create_topic_link(self, goal_id: int, topic_id: int) -> GoalTopic:
        link = GoalTopic(goal_id=goal_id, topic_id=topic_id)
        self.session.add(link)
        await self.session.flush()
        return link

    async def delete_topic_link(self, link: GoalTopic) -> None:
        await self.session.delete(link)
