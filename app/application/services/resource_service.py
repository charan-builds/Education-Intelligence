from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.resource_repository import ResourceRepository


class ResourceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.resource_repository = ResourceRepository(session)

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
