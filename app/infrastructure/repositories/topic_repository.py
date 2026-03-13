from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.question import Question
from app.domain.models.topic import Topic
from app.domain.models.topic_prerequisite import TopicPrerequisite
from app.infrastructure.cache.cache_service import CacheService


class TopicRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.cache_service = CacheService()

    async def list_topics(self) -> list[Topic]:
        result = await self.session.execute(select(Topic).order_by(Topic.id))
        return list(result.scalars().all())

    async def get_topics(self, tenant_id: int, ttl: int = 300) -> list[dict]:
        cache_key = f"tenant:{tenant_id}:topics"
        cached = await self.cache_service.get(cache_key)
        if isinstance(cached, list):
            return cached

        result = await self.session.execute(select(Topic).order_by(Topic.id))
        topics = list(result.scalars().all())
        payload = [
            {"id": topic.id, "name": topic.name, "description": topic.description}
            for topic in topics
        ]
        await self.cache_service.set(cache_key, payload, ttl=ttl)
        return payload

    async def get_topic(self, topic_id: int) -> Topic | None:
        result = await self.session.execute(select(Topic).where(Topic.id == topic_id))
        return result.scalar_one_or_none()

    async def list_topics_by_ids(self, topic_ids: list[int]) -> list[Topic]:
        if not topic_ids:
            return []
        result = await self.session.execute(select(Topic).where(Topic.id.in_(topic_ids)).order_by(Topic.id))
        return list(result.scalars().all())

    async def list_topics_by_graph_prefix(self, graph_prefix: str) -> list[Topic]:
        pattern = f"{graph_prefix}/%"
        result = await self.session.execute(
            select(Topic).where(Topic.graph_path.like(pattern)).order_by(Topic.depth.asc(), Topic.id.asc())
        )
        return list(result.scalars().all())

    async def update_topic_index(self, topic_id: int, depth: int, graph_path: str) -> None:
        await self.session.execute(
            update(Topic).where(Topic.id == topic_id).values(depth=depth, graph_path=graph_path)
        )

    async def get_prerequisite_edges(self, tenant_id: int | None = None) -> list[tuple[int, int]]:
        # Topics are global in current MVP schema; tenant_id is accepted to keep
        # graph reads tenant-aware at the API boundary and future-proof for
        # tenant-scoped topic catalogs.
        _ = tenant_id
        result = await self.session.execute(
            select(TopicPrerequisite.topic_id, TopicPrerequisite.prerequisite_topic_id)
        )
        return [(row[0], row[1]) for row in result.all()]

    async def list_questions_for_goal(self, goal_id: int | None = None) -> list[Question]:
        # Placeholder for future goal-topic mapping. Returns all questions in MVP phase.
        result = await self.session.execute(select(Question).order_by(Question.id))
        return list(result.scalars().all())

    async def get_question(self, question_id: int) -> Question | None:
        result = await self.session.execute(select(Question).where(Question.id == question_id))
        return result.scalar_one_or_none()

    async def list_questions_for_topic(self, topic_id: int) -> list[Question]:
        result = await self.session.execute(
            select(Question).where(Question.topic_id == topic_id).order_by(Question.id.asc())
        )
        return list(result.scalars().all())
