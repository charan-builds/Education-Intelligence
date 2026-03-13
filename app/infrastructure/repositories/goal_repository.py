from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.goal import Goal
from app.infrastructure.repositories.base_repository import BaseRepository


class GoalRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_all(self, limit: int, offset: int, cursor_id: int | None = None) -> list[Goal]:
        stmt = select(Goal).order_by(Goal.id.asc())
        if cursor_id is not None:
            stmt = stmt.where(Goal.id > cursor_id).limit(limit)
        else:
            stmt = self.apply_pagination(stmt, limit=limit, offset=offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(Goal.id)))
        return int(result.scalar_one())
