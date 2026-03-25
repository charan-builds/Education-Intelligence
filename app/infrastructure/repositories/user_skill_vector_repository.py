from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user_skill_vector import UserSkillVector


class UserSkillVectorRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_user_topic(self, *, tenant_id: int, user_id: int, topic_id: int) -> UserSkillVector | None:
        result = await self.session.execute(
            select(UserSkillVector).where(
                UserSkillVector.tenant_id == tenant_id,
                UserSkillVector.user_id == user_id,
                UserSkillVector.topic_id == topic_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_for_user_topic_for_update(
        self,
        *,
        tenant_id: int,
        user_id: int,
        topic_id: int,
    ) -> UserSkillVector | None:
        result = await self.session.execute(
            select(UserSkillVector)
            .where(
                UserSkillVector.tenant_id == tenant_id,
                UserSkillVector.user_id == user_id,
                UserSkillVector.topic_id == topic_id,
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, *, tenant_id: int, user_id: int) -> list[UserSkillVector]:
        result = await self.session.execute(
            select(UserSkillVector)
            .where(UserSkillVector.tenant_id == tenant_id, UserSkillVector.user_id == user_id)
            .order_by(UserSkillVector.mastery_score.desc(), UserSkillVector.topic_id.asc())
        )
        return list(result.scalars().all())

    async def upsert(
        self,
        *,
        tenant_id: int,
        user_id: int,
        topic_id: int,
        mastery_score: float,
        confidence_score: float,
        last_updated: datetime,
    ) -> UserSkillVector:
        row = await self.get_for_user_topic_for_update(tenant_id=tenant_id, user_id=user_id, topic_id=topic_id)
        if row is None:
            row = UserSkillVector(
                tenant_id=tenant_id,
                user_id=user_id,
                topic_id=topic_id,
                mastery_score=mastery_score,
                confidence_score=confidence_score,
                last_updated=last_updated,
            )
            self.session.add(row)
        else:
            row.mastery_score = mastery_score
            row.confidence_score = confidence_score
            row.last_updated = last_updated
        await self.session.flush()
        return row
