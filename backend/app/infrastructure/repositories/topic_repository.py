from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.goal_topic import GoalTopic
from app.domain.models.question import Question
from app.domain.models.topic import Topic
from app.domain.models.topic_prerequisite import TopicPrerequisite
from app.domain.models.user_answer import UserAnswer
from app.infrastructure.cache.cache_service import CacheService


class TopicRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.cache_service = CacheService()

    @staticmethod
    def _require_tenant_id(tenant_id: int | None) -> int:
        if tenant_id is None or int(tenant_id) <= 0:
            raise ValueError("tenant_id is required")
        return int(tenant_id)

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
            .options(selectinload(Question.option_rows))
            .join(Topic, Topic.id == Question.topic_id)
            .where(
                Topic.tenant_id == self._require_tenant_id(tenant_id),
                Question.is_active.is_(True),
            )
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
                .options(selectinload(Question.option_rows))
                .join(Topic, Topic.id == Question.topic_id)
                .where(
                    Topic.tenant_id == self._require_tenant_id(tenant_id),
                    Question.is_active.is_(True),
                )
                .order_by(Question.id)
            )
            fallback = await self.session.execute(fallback_stmt)
            return list(fallback.scalars().all())
        return questions

    async def get_question(
        self,
        question_id: int,
        tenant_id: int | None = None,
        *,
        active_only: bool = False,
        for_update: bool = False,
    ) -> Question | None:
        stmt = (
            select(Question)
            .options(selectinload(Question.option_rows))
            .join(Topic, Topic.id == Question.topic_id)
            .where(Question.id == question_id, Topic.tenant_id == self._require_tenant_id(tenant_id))
        )
        if active_only:
            stmt = stmt.where(Question.is_active.is_(True))
        if for_update:
            stmt = stmt.with_for_update(of=Question)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_questions_by_ids(
        self,
        *,
        tenant_id: int,
        question_ids: list[int],
        active_only: bool = True,
    ) -> list[Question]:
        if not question_ids:
            return []
        stmt = (
            select(Question)
            .options(selectinload(Question.option_rows))
            .join(Topic, Topic.id == Question.topic_id)
            .where(Question.id.in_(question_ids), Topic.tenant_id == self._require_tenant_id(tenant_id))
            .order_by(Question.id.asc())
        )
        if active_only:
            stmt = stmt.where(Question.is_active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_questions_for_topic(
        self,
        topic_id: int,
        tenant_id: int,
        *,
        active_only: bool = True,
    ) -> list[Question]:
        stmt = (
            select(Question)
            .options(selectinload(Question.option_rows))
            .join(Topic, Topic.id == Question.topic_id)
            .where(Question.topic_id == topic_id, Topic.tenant_id == self._require_tenant_id(tenant_id))
            .order_by(Question.id.asc())
        )
        if active_only:
            stmt = stmt.where(Question.is_active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_questions_for_topics(
        self,
        *,
        tenant_id: int,
        topic_ids: list[int],
        exclude_question_ids: list[int] | None = None,
        goal_id: int | None = None,
    ) -> list[Question]:
        if not topic_ids:
            return []
        stmt = (
            select(Question)
            .options(selectinload(Question.option_rows))
            .join(Topic, Topic.id == Question.topic_id)
            .where(
                Topic.tenant_id == self._require_tenant_id(tenant_id),
                Question.topic_id.in_(topic_ids),
                Question.is_active.is_(True),
            )
            .order_by(Question.topic_id.asc(), Question.difficulty_level.asc(), Question.id.asc())
        )
        if exclude_question_ids:
            stmt = stmt.where(~Question.id.in_(exclude_question_ids))
        if goal_id is not None:
            mapped_topic_ids = select(GoalTopic.topic_id).where(GoalTopic.goal_id == goal_id)
            stmt = stmt.where(Question.topic_id.in_(mapped_topic_ids))
        result = await self.session.execute(stmt)
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
        stmt = (
            select(Question)
            .options(selectinload(Question.option_rows))
            .join(Topic, Topic.id == Question.topic_id)
            .where(
                Topic.tenant_id == self._require_tenant_id(tenant_id),
                Question.is_active.is_(True),
            )
            .order_by(Question.id.asc())
        )
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
        stmt = (
            select(func.count(Question.id))
            .join(Topic, Topic.id == Question.topic_id)
            .where(
                Topic.tenant_id == self._require_tenant_id(tenant_id),
                Question.is_active.is_(True),
            )
        )
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

    async def count_answers_for_question(self, question_id: int, tenant_id: int) -> int:
        stmt = (
            select(func.count(UserAnswer.id))
            .join(Question, Question.id == UserAnswer.question_id)
            .join(Topic, Topic.id == Question.topic_id)
            .where(
                UserAnswer.question_id == question_id,
                Topic.tenant_id == self._require_tenant_id(tenant_id),
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
        options: list[dict] | None = None,
    ) -> Question:
        question = Question(
            topic_id=topic_id,
            difficulty=difficulty,
            question_type=question_type,
            question_text=question_text,
            correct_answer=correct_answer,
            accepted_answers=accepted_answers,
            version=1,
            is_active=True,
        )
        question.options = options if options is not None else answer_options
        self.session.add(question)
        await self.session.flush()
        return question

    async def update_question(self, question: Question, **updates) -> Question:
        next_updates = dict(updates)
        for reserved_field in ("id", "topic_id", "version", "is_active", "created_at", "updated_at"):
            next_updates.pop(reserved_field, None)
        correct_answer_changed = "correct_answer" in next_updates
        correct_answer = next_updates.pop("correct_answer", question.correct_answer)

        if "options" in next_updates:
            option_values = next_updates.pop("options")
        elif "answer_options" in next_updates:
            option_values = next_updates.pop("answer_options")
        elif correct_answer_changed:
            option_values = list(question.answer_options or [])
        else:
            option_values = list(question.options or [])

        difficulty = next_updates.pop(
            "difficulty",
            getattr(question, "difficulty_level", getattr(question, "difficulty", 2)),
        )
        question_type = next_updates.pop("question_type", question.question_type)
        question_text = next_updates.pop("question_text", question.question_text)
        accepted_answers = next_updates.pop("accepted_answers", list(question.accepted_answers or []))
        explanation = next_updates.pop("explanation", getattr(question, "explanation", None))

        await self.session.execute(update(Question).where(Question.id == question.id).values(is_active=False))
        new_question = Question(
            topic_id=question.topic_id,
            version=int(question.version or 1) + 1,
            is_active=True,
            difficulty=difficulty,
            question_type=question_type,
            question_text=question_text,
            correct_answer=correct_answer,
            accepted_answers=list(accepted_answers or []),
            explanation=explanation,
        )
        new_question.options = option_values
        for field, value in next_updates.items():
            setattr(new_question, field, value)
        self.session.add(new_question)
        await self.session.flush()
        return new_question

    async def delete_question(self, question: Question) -> None:
        await self.session.execute(update(Question).where(Question.id == question.id).values(is_active=False))
        await self.session.flush()
