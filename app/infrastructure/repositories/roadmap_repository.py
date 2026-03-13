from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.roadmap import Roadmap
from app.domain.models.roadmap_step import RoadmapStep
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.tenant_scoping import tenant_user_scope


class RoadmapRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_roadmap(self, user_id: int, goal_id: int, generated_at: datetime) -> Roadmap:
        roadmap = Roadmap(user_id=user_id, goal_id=goal_id, generated_at=generated_at)
        self.session.add(roadmap)
        await self.session.flush()
        return roadmap

    async def add_step(
        self,
        roadmap_id: int,
        topic_id: int,
        deadline: datetime,
        estimated_time_hours: float = 4.0,
        difficulty: str = "medium",
        priority: int = 1,
        progress_status: str = "pending",
    ) -> RoadmapStep:
        step = RoadmapStep(
            roadmap_id=roadmap_id,
            topic_id=topic_id,
            estimated_time_hours=estimated_time_hours,
            difficulty=difficulty,
            priority=priority,
            deadline=deadline,
            progress_status=progress_status,
        )
        self.session.add(step)
        await self.session.flush()
        return step

    async def list_user_roadmaps(
        self,
        user_id: int,
        tenant_id: int,
        limit: int,
        offset: int,
        cursor_id: int | None = None,
    ) -> list[Roadmap]:
        stmt = (
            select(Roadmap)
            .options(selectinload(Roadmap.steps))
            .join(Roadmap.user)
            .where(Roadmap.user_id == user_id, tenant_user_scope(Roadmap.user, tenant_id))
            .order_by(Roadmap.id.desc())
        )
        if cursor_id is not None:
            stmt = stmt.where(Roadmap.id < cursor_id).limit(limit)
        else:
            stmt = self.apply_pagination(stmt, limit=limit, offset=offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_user_roadmaps(self, user_id: int, tenant_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Roadmap.id))
            .join(Roadmap.user)
            .where(Roadmap.user_id == user_id, tenant_user_scope(Roadmap.user, tenant_id))
        )
        return int(result.scalar_one())
