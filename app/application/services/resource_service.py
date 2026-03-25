from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import NotFoundError
from app.infrastructure.repositories.goal_repository import GoalRepository
from app.infrastructure.repositories.resource_repository import ResourceRepository
from app.infrastructure.repositories.topic_repository import TopicRepository


class ResourceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.resource_repository = ResourceRepository(session)
        self.topic_repository = TopicRepository(session)
        self.goal_repository = GoalRepository(session)

    async def _get_topic(self, tenant_id: int, topic_id: int):
        return await self.topic_repository.get_topic(topic_id, tenant_id=tenant_id)

    async def _get_goal(self, tenant_id: int, goal_id: int):
        return await self.goal_repository.get_by_id(tenant_id, goal_id)

    async def _validate_resource_scope(self, *, tenant_id: int, topic_id: int, goal_id: int | None) -> None:
        topic = await self._get_topic(tenant_id, topic_id)
        if topic is None:
            raise NotFoundError("Topic not found")
        if goal_id is not None:
            goal = await self._get_goal(tenant_id, goal_id)
            if goal is None:
                raise NotFoundError("Goal not found")

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
    ):
        try:
            await self._validate_resource_scope(
                tenant_id=tenant_id,
                topic_id=topic_id,
                goal_id=goal_id,
            )
            resource = await self.resource_repository.add_resource(
                tenant_id=tenant_id,
                topic_id=topic_id,
                goal_id=goal_id,
                resource_type=resource_type,
                title=title,
                url=url,
                difficulty=difficulty,
                rating=rating,
                goal_relevance=goal_relevance,
                description=description,
            )
            await self.session.commit()
            return resource
        except Exception:
            await self.session.rollback()
            raise

    async def search_resources_by_topic(
        self,
        *,
        tenant_id: int,
        topic_id: int,
        difficulty: str | None = None,
        min_rating: float | None = None,
        min_goal_relevance: float | None = None,
        goal_id: int | None = None,
    ):
        await self._validate_resource_scope(
            tenant_id=tenant_id,
            topic_id=topic_id,
            goal_id=goal_id,
        )
        return await self.resource_repository.search_resources_by_topic(
            tenant_id=tenant_id,
            topic_id=topic_id,
            difficulty=difficulty,
            min_rating=min_rating,
            min_goal_relevance=min_goal_relevance,
            goal_id=goal_id,
        )

    async def recommend_resources_for_user(
        self,
        *,
        tenant_id: int,
        topic_scores: dict[int, float],
        goal_id: int | None = None,
        difficulty: str | None = None,
        min_rating: float | None = None,
        min_goal_relevance: float | None = None,
        per_topic_limit: int = 2,
    ) -> list:
        if not topic_scores:
            return []

        unique_topic_ids = sorted({int(topic_id) for topic_id in topic_scores})
        for topic_id in unique_topic_ids:
            if await self._get_topic(tenant_id, topic_id) is None:
                raise NotFoundError(f"Topic {topic_id} not found")
        if goal_id is not None and await self._get_goal(tenant_id, goal_id) is None:
            raise NotFoundError("Goal not found")

        ordered_topics = sorted(topic_scores.items(), key=lambda kv: (kv[1], kv[0]))
        weak_first_topic_ids = [topic_id for topic_id, score in ordered_topics if score <= 70]
        if not weak_first_topic_ids:
            weak_first_topic_ids = [topic_id for topic_id, _ in ordered_topics]

        resources = await self.resource_repository.recommend_resources_for_topics(
            tenant_id=tenant_id,
            topic_ids=weak_first_topic_ids,
            difficulty=difficulty,
            min_rating=min_rating,
            min_goal_relevance=min_goal_relevance,
            goal_id=goal_id,
        )

        grouped: dict[int, list] = {topic_id: [] for topic_id in weak_first_topic_ids}
        for resource in resources:
            bucket = grouped.get(resource.topic_id)
            if bucket is None or len(bucket) >= per_topic_limit:
                continue
            bucket.append(resource)

        ordered: list = []
        for topic_id in weak_first_topic_ids:
            ordered.extend(grouped[topic_id])
        return ordered
