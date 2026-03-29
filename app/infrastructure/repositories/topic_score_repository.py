from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.topic_score import TopicScore
from app.infrastructure.repositories.base_repository import BaseRepository


class TopicScoreRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_by_user(self, *, tenant_id: int, user_id: int) -> list[TopicScore]:
        result = await self.session.execute(
            select(TopicScore)
            .where(
                TopicScore.tenant_id == tenant_id,
                TopicScore.user_id == user_id,
            )
            .order_by(TopicScore.score.asc(), TopicScore.topic_id.asc())
        )
        return list(result.scalars().all())
