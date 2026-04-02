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

    @staticmethod
    def _require_tenant_id(tenant_id: int | None) -> int:
        if tenant_id is None or int(tenant_id) <= 0:
            raise ValueError("tenant_id is required")
        return int(tenant_id)

    async def create_roadmap(
        self,
        user_id: int,
        goal_id: int,
        test_id: int,
        generated_at: datetime,
        status: str = "generating",
        error_message: str | None = None,
    ) -> Roadmap:
        roadmap = Roadmap(
            user_id=user_id,
            goal_id=goal_id,
            test_id=test_id,
            generated_at=generated_at,
            status=status,
            error_message=error_message,
        )
        self.session.add(roadmap)
        await self.session.flush()
        return roadmap

    async def get_by_identity(
        self,
        *,
        user_id: int,
        goal_id: int,
        test_id: int,
        tenant_id: int,
        for_update: bool = False,
    ) -> Roadmap | None:
        stmt = (
            select(Roadmap)
            .options(selectinload(Roadmap.steps))
            .join(Roadmap.user)
            .where(
                Roadmap.user_id == user_id,
                Roadmap.goal_id == goal_id,
                Roadmap.test_id == test_id,
                tenant_user_scope(Roadmap.user, self._require_tenant_id(tenant_id)),
            )
            .limit(1)
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_step(
        self,
        roadmap_id: int,
        topic_id: int,
        deadline: datetime,
        estimated_time_hours: float = 4.0,
        difficulty: str = "medium",
        priority: int = 1,
        progress_status: str = "pending",
        step_type: str = "core",
        rationale: str | None = None,
        unlocks_topic_id: int | None = None,
        is_revision: bool = False,
    ) -> RoadmapStep:
        step = RoadmapStep(
            roadmap_id=roadmap_id,
            topic_id=topic_id,
            estimated_time_hours=estimated_time_hours,
            difficulty=difficulty,
            priority=priority,
            deadline=deadline,
            progress_status=progress_status,
            step_type=step_type,
            rationale=rationale,
            unlocks_topic_id=unlocks_topic_id,
            is_revision=is_revision,
        )
        self.session.add(step)
        await self.session.flush()
        return step

    async def get_latest_roadmap_for_user(self, *, user_id: int, tenant_id: int) -> Roadmap | None:
        stmt = (
            select(Roadmap)
            .options(selectinload(Roadmap.steps))
            .join(Roadmap.user)
            .where(Roadmap.user_id == user_id, tenant_user_scope(Roadmap.user, self._require_tenant_id(tenant_id)))
            .order_by(Roadmap.id.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_status(self, roadmap: Roadmap, *, status: str, error_message: str | None = None) -> Roadmap:
        roadmap.status = status
        roadmap.error_message = error_message
        await self.session.flush()
        return roadmap

    async def clear_steps(self, roadmap: Roadmap) -> None:
        for step in list(roadmap.steps):
            await self.session.delete(step)
        await self.session.flush()

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
            .where(Roadmap.user_id == user_id, tenant_user_scope(Roadmap.user, self._require_tenant_id(tenant_id)))
            .order_by(Roadmap.id.desc())
        )
        if cursor_id is not None:
            stmt = stmt.where(Roadmap.id < cursor_id).limit(limit)
        else:
            stmt = self.apply_pagination(stmt, limit=limit, offset=offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_roadmap_for_user(self, *, roadmap_id: int, user_id: int, tenant_id: int) -> Roadmap | None:
        stmt = (
            select(Roadmap)
            .options(selectinload(Roadmap.steps))
            .join(Roadmap.user)
            .where(
                Roadmap.id == roadmap_id,
                Roadmap.user_id == user_id,
                tenant_user_scope(Roadmap.user, self._require_tenant_id(tenant_id)),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_user_roadmaps(self, user_id: int, tenant_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Roadmap.id))
            .join(Roadmap.user)
            .where(Roadmap.user_id == user_id, tenant_user_scope(Roadmap.user, self._require_tenant_id(tenant_id)))
        )
        return int(result.scalar_one())

    async def get_step_for_user(self, *, step_id: int, user_id: int, tenant_id: int) -> RoadmapStep | None:
        stmt = (
            select(RoadmapStep)
            .join(RoadmapStep.roadmap)
            .join(Roadmap.user)
            .where(
                RoadmapStep.id == step_id,
                Roadmap.user_id == user_id,
                tenant_user_scope(Roadmap.user, self._require_tenant_id(tenant_id)),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_step_status(self, step: RoadmapStep, *, progress_status: str) -> RoadmapStep:
        step.progress_status = progress_status
        await self.session.flush()
        return step
