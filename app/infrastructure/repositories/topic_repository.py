from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.goal_topic import GoalTopic
from app.domain.models.question import Question
from app.domain.models.topic import Topic
from app.domain.models.topic_prerequisite import TopicPrerequisite
from app.infrastructure.cache.cache_service import CacheService


class TopicRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.cache_service = CacheService()

    @staticmethod
    def _require_tenant_id(tenant_id: int | None) -> int:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        return tenant_id

    async def list_topics(self, tenant_id: int) -> list[Topic]:
        stmt = select(Topic).where(Topic.tenant_id == self._require_tenant_id(tenant_id)).order_by(Topic.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_topics(self, tenant_id: int, ttl: int = 300) -> list[dict]:
        cache_key = await self.cache_service.build_tenant_versioned_key("topics", tenant_id=tenant_id)
        cached = await self.cache_service.get(cache_key)
        if isinstance(cached, list):
            return cached

        result = await self.session.execute(select(Topic).where(Topic.tenant_id == tenant_id).order_by(Topic.id))
        topics = list(result.scalars().all())
        payload = [
            {"id": topic.id, "tenant_id": topic.tenant_id, "name": topic.name, "description": topic.description}
            for topic in topics
        ]
        await self.cache_service.set(cache_key, payload, ttl=ttl)
        return payload

    async def invalidate_topics_cache(self, tenant_id: int) -> None:
        await self.cache_service.bump_namespace_version(f"topics:tenant:{tenant_id}")

    async def get_topic(self, topic_id: int, tenant_id: int) -> Topic | None:
        stmt = select(Topic).where(Topic.id == topic_id, Topic.tenant_id == self._require_tenant_id(tenant_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_topic_by_name(self, tenant_id: int, name: str) -> Topic | None:
        result = await self.session.execute(select(Topic).where(Topic.tenant_id == tenant_id, Topic.name == name))
        return result.scalar_one_or_none()

    async def list_topics_by_ids(self, topic_ids: list[int], tenant_id: int) -> list[Topic]:
        if not topic_ids:
            return []
        stmt = select(Topic).where(Topic.id.in_(topic_ids), Topic.tenant_id == self._require_tenant_id(tenant_id))
        result = await self.session.execute(stmt.order_by(Topic.id))
        return list(result.scalars().all())

    async def get_prerequisite_link(
        self,
        topic_id: int,
        prerequisite_topic_id: int,
        tenant_id: int,
    ) -> TopicPrerequisite | None:
        stmt = select(TopicPrerequisite).where(
            TopicPrerequisite.topic_id == topic_id,
            TopicPrerequisite.prerequisite_topic_id == prerequisite_topic_id,
        )
        stmt = stmt.join(Topic, Topic.id == TopicPrerequisite.topic_id).where(
            Topic.tenant_id == self._require_tenant_id(tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_prerequisite_link_by_id(self, prerequisite_id: int, tenant_id: int) -> TopicPrerequisite | None:
        stmt = select(TopicPrerequisite).where(TopicPrerequisite.id == prerequisite_id)
        stmt = stmt.join(Topic, Topic.id == TopicPrerequisite.topic_id).where(
            Topic.tenant_id == self._require_tenant_id(tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_prerequisite_links(
        self, limit: int, offset: int, topic_id: int | None = None, tenant_id: int | None = None
    ) -> list[TopicPrerequisite]:
        stmt = select(TopicPrerequisite).order_by(
            TopicPrerequisite.topic_id.asc(), TopicPrerequisite.prerequisite_topic_id.asc()
        )
        if topic_id is not None:
            stmt = stmt.where(TopicPrerequisite.topic_id == topic_id)
        stmt = stmt.join(Topic, Topic.id == TopicPrerequisite.topic_id).where(
            Topic.tenant_id == self._require_tenant_id(tenant_id)
        )
        result = await self.session.execute(stmt.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def count_prerequisite_links(self, topic_id: int | None = None, tenant_id: int | None = None) -> int:
        stmt = select(func.count(TopicPrerequisite.id))
        if topic_id is not None:
            stmt = stmt.where(TopicPrerequisite.topic_id == topic_id)
        stmt = stmt.join(Topic, Topic.id == TopicPrerequisite.topic_id).where(
            Topic.tenant_id == self._require_tenant_id(tenant_id)
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def list_topics_by_graph_prefix(self, graph_prefix: str, tenant_id: int) -> list[Topic]:
        pattern = f"{graph_prefix}/%"
        stmt = select(Topic).where(Topic.graph_path.like(pattern), Topic.tenant_id == self._require_tenant_id(tenant_id))
        result = await self.session.execute(stmt.order_by(Topic.depth.asc(), Topic.id.asc()))
        return list(result.scalars().all())

    async def update_topic_index(self, topic_id: int, depth: int, graph_path: str, tenant_id: int) -> None:
        stmt = update(Topic).where(Topic.id == topic_id, Topic.tenant_id == self._require_tenant_id(tenant_id))
        await self.session.execute(stmt.values(depth=depth, graph_path=graph_path))

    async def get_prerequisite_edges(self, tenant_id: int) -> list[tuple[int, int]]:
        stmt = select(TopicPrerequisite.topic_id, TopicPrerequisite.prerequisite_topic_id)
        stmt = stmt.join(Topic, Topic.id == TopicPrerequisite.topic_id).where(
            Topic.tenant_id == self._require_tenant_id(tenant_id)
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def create_prerequisite_link(self, topic_id: int, prerequisite_topic_id: int) -> TopicPrerequisite:
        link = TopicPrerequisite(topic_id=topic_id, prerequisite_topic_id=prerequisite_topic_id)
        self.session.add(link)
        await self.session.flush()
        return link

    async def delete_prerequisite_link(self, link: TopicPrerequisite) -> None:
        await self.session.delete(link)

    async def list_questions_for_goal(self, goal_id: int | None = None, tenant_id: int | None = None) -> list[Question]:
        stmt = (
            select(Question)
            .join(Topic, Topic.id == Question.topic_id)
            .where(Topic.tenant_id == self._require_tenant_id(tenant_id))
            .order_by(Question.id)
        )
        if goal_id is not None:
            mapped_topic_ids = select(GoalTopic.topic_id).where(GoalTopic.goal_id == goal_id)
            stmt = stmt.where(Question.topic_id.in_(mapped_topic_ids))
        result = await self.session.execute(stmt)
        questions = list(result.scalars().all())
        if goal_id is not None and not questions:
            fallback_stmt = (
                select(Question)
                .join(Topic, Topic.id == Question.topic_id)
                .where(Topic.tenant_id == self._require_tenant_id(tenant_id))
                .order_by(Question.id)
            )
            fallback = await self.session.execute(fallback_stmt)
            return list(fallback.scalars().all())
        return questions

    async def get_question(self, question_id: int, tenant_id: int | None = None) -> Question | None:
        stmt = select(Question).where(Question.id == question_id)
        if tenant_id is not None:
            stmt = stmt.join(Topic, Topic.id == Question.topic_id).where(
                Topic.tenant_id == self._require_tenant_id(tenant_id)
            )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_questions_by_ids(self, *, tenant_id: int, question_ids: list[int]) -> list[Question]:
        if not question_ids:
            return []
        result = await self.session.execute(
            select(Question)
            .join(Topic, Topic.id == Question.topic_id)
            .where(Question.id.in_(question_ids), Topic.tenant_id == self._require_tenant_id(tenant_id))
            .order_by(Question.id.asc())
        )
        return list(result.scalars().all())

    async def list_questions_for_topic(self, topic_id: int, tenant_id: int) -> list[Question]:
        result = await self.session.execute(
            select(Question)
            .join(Topic, Topic.id == Question.topic_id)
            .where(Question.topic_id == topic_id, Topic.tenant_id == self._require_tenant_id(tenant_id))
            .order_by(Question.id.asc())
        )
        return list(result.scalars().all())

    async def create_topic(self, tenant_id: int, name: str, description: str) -> Topic:
        topic = Topic(tenant_id=tenant_id, name=name, description=description)
        self.session.add(topic)
        await self.session.flush()
        return topic

    async def update_topic(self, topic: Topic, **updates) -> Topic:
        for field, value in updates.items():
            setattr(topic, field, value)
        await self.session.flush()
        return topic

    async def delete_topic(self, topic: Topic) -> None:
        await self.session.delete(topic)

    async def list_questions(
        self,
        limit: int,
        offset: int,
        tenant_id: int,
        topic_id: int | None = None,
        question_type: str | None = None,
        search: str | None = None,
    ) -> list[Question]:
        stmt = select(Question).join(Topic, Topic.id == Question.topic_id).where(Topic.tenant_id == tenant_id).order_by(Question.id.asc())
        if topic_id is not None:
            stmt = stmt.where(Question.topic_id == topic_id)
        if question_type is not None:
            stmt = stmt.where(Question.question_type == question_type)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Question.question_text.ilike(pattern),
                    Question.correct_answer.ilike(pattern),
                )
            )
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_questions(
        self,
        tenant_id: int,
        topic_id: int | None = None,
        question_type: str | None = None,
        search: str | None = None,
    ) -> int:
        stmt = select(func.count(Question.id)).join(Topic, Topic.id == Question.topic_id).where(Topic.tenant_id == tenant_id)
        if topic_id is not None:
            stmt = stmt.where(Question.topic_id == topic_id)
        if question_type is not None:
            stmt = stmt.where(Question.question_type == question_type)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Question.question_text.ilike(pattern),
                    Question.correct_answer.ilike(pattern),
                )
            )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create_question(
        self,
        topic_id: int,
        difficulty: int,
        question_type: str,
        question_text: str,
        correct_answer: str,
        accepted_answers: list[str],
        answer_options: list[str],
    ) -> Question:
        question = Question(
            topic_id=topic_id,
            difficulty=difficulty,
            question_type=question_type,
            question_text=question_text,
            correct_answer=correct_answer,
            accepted_answers=accepted_answers,
            answer_options=answer_options,
        )
        self.session.add(question)
        await self.session.flush()
        return question

    async def update_question(self, question: Question, **updates) -> Question:
        for field, value in updates.items():
            setattr(question, field, value)
        await self.session.flush()
        return question

    async def delete_question(self, question: Question) -> None:
        await self.session.delete(question)
