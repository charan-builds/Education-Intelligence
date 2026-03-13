from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.resource import Resource


class ResourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_resource(
        self,
        *,
        tenant_id: int,
        topic_id: int,
        goal_id: int | None,
        resource_type: str,
        title: str,
        url: str,
        difficulty: str,
        rating: float,
        goal_relevance: float,
        description: str | None = None,
    ) -> Resource:
        resource = Resource(
            tenant_id=tenant_id,
            topic_id=topic_id,
            goal_id=goal_id,
            resource_type=resource_type,
            title=title,
            url=url,
            difficulty=difficulty,
            rating=rating,
            goal_relevance=goal_relevance,
            created_at=datetime.now(timezone.utc),
            description=description,
        )
        self.session.add(resource)
        await self.session.flush()
        return resource

    async def search_resources_by_topic(
        self,
        *,
        tenant_id: int,
        topic_id: int,
        difficulty: str | None = None,
        min_rating: float | None = None,
        min_goal_relevance: float | None = None,
        goal_id: int | None = None,
    ) -> list[Resource]:
        stmt: Select = select(Resource).where(
            Resource.tenant_id == tenant_id,
            Resource.topic_id == topic_id,
        )
        stmt = self._apply_filters(
            stmt,
            difficulty=difficulty,
            min_rating=min_rating,
            min_goal_relevance=min_goal_relevance,
            goal_id=goal_id,
        )
        stmt = stmt.order_by(Resource.rating.desc(), Resource.goal_relevance.desc(), Resource.id.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def recommend_resources_for_topics(
        self,
        *,
        tenant_id: int,
        topic_ids: list[int],
        difficulty: str | None = None,
        min_rating: float | None = None,
        min_goal_relevance: float | None = None,
        goal_id: int | None = None,
    ) -> list[Resource]:
        if not topic_ids:
            return []

        stmt: Select = select(Resource).where(
            Resource.tenant_id == tenant_id,
            Resource.topic_id.in_(topic_ids),
        )
        stmt = self._apply_filters(
            stmt,
            difficulty=difficulty,
            min_rating=min_rating,
            min_goal_relevance=min_goal_relevance,
            goal_id=goal_id,
        )
        stmt = stmt.order_by(Resource.topic_id.asc(), Resource.rating.desc(), Resource.goal_relevance.desc(), Resource.id.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def _apply_filters(
        stmt: Select,
        *,
        difficulty: str | None,
        min_rating: float | None,
        min_goal_relevance: float | None,
        goal_id: int | None,
    ) -> Select:
        predicates = []
        if difficulty is not None:
            predicates.append(Resource.difficulty == difficulty)
        if min_rating is not None:
            predicates.append(Resource.rating >= min_rating)
        if min_goal_relevance is not None:
            predicates.append(Resource.goal_relevance >= min_goal_relevance)
        if goal_id is not None:
            predicates.append(Resource.goal_id == goal_id)
        if predicates:
            stmt = stmt.where(and_(*predicates))
        return stmt
