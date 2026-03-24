import asyncio
from types import SimpleNamespace

import pytest

from app.application.exceptions import ConflictError, NotFoundError, ValidationError
from app.application.services.topic_service import TopicService


class _Session:
    async def commit(self):
        return None

    async def rollback(self):
        return None


class _Repository:
    last_list_args = None
    last_count_args = None

    def __init__(self):
        self.session = _Session()
        self.topic = SimpleNamespace(id=1, name="Topic 1")
        self.topic_two = SimpleNamespace(id=2, name="Topic 2")
        self.topics_by_name = {"Topic 1": self.topic}
        self.prerequisite_link = None
        self.question = SimpleNamespace(
            id=1,
            topic_id=1,
            difficulty=1,
            question_type="multiple_choice",
            question_text="What is 2 + 2?",
            correct_answer="4",
            accepted_answers=["four"],
            answer_options=["3", "4", "5"],
        )

    async def get_topic(self, topic_id: int):
        if topic_id == 1:
            return self.topic
        if topic_id == 2:
            return self.topic_two
        return None

    async def get_topic_by_name(self, name: str):
        return self.topics_by_name.get(name)

    async def get_prerequisite_link(self, topic_id: int, prerequisite_topic_id: int):
        if self.prerequisite_link and (
            self.prerequisite_link.topic_id == topic_id
            and self.prerequisite_link.prerequisite_topic_id == prerequisite_topic_id
        ):
            return self.prerequisite_link
        return None

    async def get_prerequisite_link_by_id(self, prerequisite_id: int):
        if self.prerequisite_link and self.prerequisite_link.id == prerequisite_id:
            return self.prerequisite_link
        return None

    async def get_topics(self, tenant_id: int, ttl: int = 300):
        _ = tenant_id, ttl
        return [
            {"id": 1, "name": "Linear Algebra", "description": "Vectors"},
            {"id": 2, "name": "Statistics", "description": "Probability"},
        ]

    async def create_question(self, **kwargs):
        if kwargs["question_type"] == "multiple_choice" and not kwargs["answer_options"]:
            raise ValueError("multiple_choice questions require non-empty answer_options")
        return SimpleNamespace(id=2, **kwargs)

    async def create_prerequisite_link(self, topic_id: int, prerequisite_topic_id: int):
        self.prerequisite_link = SimpleNamespace(
            id=5,
            topic_id=topic_id,
            prerequisite_topic_id=prerequisite_topic_id,
        )
        return self.prerequisite_link

    async def create_topic(self, name: str, description: str):
        return SimpleNamespace(id=2, name=name, description=description)

    async def get_question(self, question_id: int):
        return self.question if question_id == 1 else None

    async def update_topic(self, topic, **updates):
        for key, value in updates.items():
            setattr(topic, key, value)
        return topic

    async def update_question(self, question, **updates):
        for key, value in updates.items():
            setattr(question, key, value)
        if question.question_type == "multiple_choice" and not question.answer_options:
            raise ValueError("multiple_choice questions require non-empty answer_options")
        return question

    async def delete_question(self, question):
        _ = question
        return None

    async def delete_topic(self, topic):
        _ = topic
        return None

    async def delete_prerequisite_link(self, link):
        self.prerequisite_link = None
        _ = link
        return None

    async def list_questions_for_topic(self, topic_id: int):
        _ = topic_id
        return [self.question]

    async def list_prerequisite_links(self, limit: int, offset: int, topic_id: int | None = None):
        _ = limit, offset, topic_id
        return [self.prerequisite_link] if self.prerequisite_link else []

    async def count_prerequisite_links(self, topic_id: int | None = None):
        _ = topic_id
        return 1 if self.prerequisite_link else 0

    async def get_prerequisite_edges(self, tenant_id=None):
        _ = tenant_id
        if self.prerequisite_link is None:
            return []
        return [(self.prerequisite_link.topic_id, self.prerequisite_link.prerequisite_topic_id)]

    async def list_questions(
        self,
        limit: int,
        offset: int,
        topic_id: int | None = None,
        question_type: str | None = None,
        search: str | None = None,
    ):
        self.last_list_args = {
            "limit": limit,
            "offset": offset,
            "topic_id": topic_id,
            "question_type": question_type,
            "search": search,
        }
        return [self.question]

    async def count_questions(
        self,
        topic_id: int | None = None,
        question_type: str | None = None,
        search: str | None = None,
    ):
        self.last_count_args = {
            "topic_id": topic_id,
            "question_type": question_type,
            "search": search,
        }
        return 1


def test_create_question_validates_topic_exists():
    async def _run():
        service = TopicService(session=SimpleNamespace())
        service.repository = _Repository()

        with pytest.raises(NotFoundError):
            await service.create_question(
                topic_id=999,
                difficulty=1,
                question_type="multiple_choice",
                question_text="Question?",
                correct_answer="A",
                accepted_answers=[],
                answer_options=["A", "B"],
            )

    asyncio.run(_run())


def test_create_question_maps_model_validation_error():
    async def _run():
        service = TopicService(session=SimpleNamespace())
        service.repository = _Repository()

        with pytest.raises(ValidationError):
            await service.create_question(
                topic_id=1,
                difficulty=1,
                question_type="multiple_choice",
                question_text="Question?",
                correct_answer="A",
                accepted_answers=[],
                answer_options=[],
            )

    asyncio.run(_run())


def test_list_questions_page_returns_metadata():
    async def _run():
        service = TopicService(session=SimpleNamespace())
        service.repository = _Repository()

        page = await service.list_questions_page(limit=20, offset=0, topic_id=1)
        assert page["meta"]["total"] == 1
        assert len(page["items"]) == 1

    asyncio.run(_run())


def test_list_questions_page_passes_filters_to_repository():
    async def _run():
        service = TopicService(session=SimpleNamespace())
        repository = _Repository()
        service.repository = repository

        page = await service.list_questions_page(
            limit=10,
            offset=20,
            topic_id=1,
            question_type="multiple_choice",
            search="probability",
        )
        assert page["meta"]["offset"] == 20
        assert repository.last_list_args == {
            "limit": 10,
            "offset": 20,
            "topic_id": 1,
            "question_type": "multiple_choice",
            "search": "probability",
        }
        assert repository.last_count_args == {
            "topic_id": 1,
            "question_type": "multiple_choice",
            "search": "probability",
        }

    asyncio.run(_run())


def test_list_topics_page_returns_metadata():
    async def _run():
        service = TopicService(session=SimpleNamespace())
        service.repository = _Repository()

        page = await service.list_topics_page(limit=1, offset=0, tenant_id=10)
        assert page["meta"]["total"] == 2
        assert page["meta"]["next_offset"] == 1
        assert page["items"][0]["name"] == "Linear Algebra"

    asyncio.run(_run())


def test_create_topic_rejects_duplicate_name():
    async def _run():
        service = TopicService(session=SimpleNamespace())
        service.repository = _Repository()

        with pytest.raises(ConflictError):
            await service.create_topic(name="Topic 1", description="Duplicate")

    asyncio.run(_run())


def test_create_topic_returns_created_topic():
    async def _run():
        service = TopicService(session=SimpleNamespace())
        repository = _Repository()
        repository.topics_by_name = {}
        service.repository = repository

        topic = await service.create_topic(name="New Topic", description="Fresh")
        assert topic.name == "New Topic"
        assert topic.description == "Fresh"

    asyncio.run(_run())


def test_delete_topic_with_questions_is_blocked():
    async def _run():
        service = TopicService(session=SimpleNamespace())
        service.repository = _Repository()

        with pytest.raises(ValidationError):
            await service.delete_topic(1)

    asyncio.run(_run())


def test_create_prerequisite_blocks_self_dependency():
    async def _run():
        service = TopicService(session=SimpleNamespace())
        service.repository = _Repository()

        with pytest.raises(ValidationError):
            await service.create_prerequisite(topic_id=1, prerequisite_topic_id=1)

    asyncio.run(_run())


def test_create_prerequisite_returns_created_link():
    async def _run():
        service = TopicService(session=SimpleNamespace())
        repository = _Repository()
        service.repository = repository

        link = await service.create_prerequisite(topic_id=1, prerequisite_topic_id=2)
        assert link.id == 5
        assert link.topic_id == 1
        assert link.prerequisite_topic_id == 2

    asyncio.run(_run())


def test_create_prerequisite_blocks_duplicate_link():
    async def _run():
        service = TopicService(session=SimpleNamespace())
        repository = _Repository()
        repository.prerequisite_link = SimpleNamespace(id=5, topic_id=1, prerequisite_topic_id=2)
        service.repository = repository

        with pytest.raises(ConflictError):
            await service.create_prerequisite(topic_id=1, prerequisite_topic_id=2)

    asyncio.run(_run())


def test_import_questions_returns_created_count():
    async def _run():
        service = TopicService(session=SimpleNamespace())
        service.repository = _Repository()

        created = await service.import_questions(
            [
                {
                    "topic_id": 1,
                    "difficulty": 1,
                    "question_type": "multiple_choice",
                    "question_text": "New question?",
                    "correct_answer": "A",
                    "accepted_answers": [],
                    "answer_options": ["A", "B"],
                }
            ]
        )
        assert created == 1

    asyncio.run(_run())


def test_import_questions_csv_returns_created_count():
    async def _run():
        service = TopicService(session=SimpleNamespace())
        service.repository = _Repository()

        created = await service.import_questions_csv(
            "topic_id,difficulty,question_type,question_text,correct_answer,accepted_answers,answer_options\n"
            "1,1,multiple_choice,New question?,A,,A|B\n"
        )
        assert created == 1

    asyncio.run(_run())


def test_export_questions_csv_contains_headers_and_pipe_joined_lists():
    async def _run():
        service = TopicService(session=SimpleNamespace())
        service.repository = _Repository()

        content = await service.export_questions_csv(topic_id=1)
        assert "topic_id" in content
        assert "accepted_answers" in content
        assert "four" in content
        assert "3|4|5" in content

    asyncio.run(_run())


def test_tenant_scoped_topic_lookup_hides_foreign_topic():
    class _TenantAwareRepository(_Repository):
        async def get_topic(self, topic_id: int, tenant_id: int | None = None):
            if tenant_id == 1:
                return await super().get_topic(topic_id)
            return None

        async def get_topic_by_name(self, tenant_id: int, name: str):
            if tenant_id == 1:
                return await super().get_topic_by_name(name)
            return None

    async def _run():
        service = TopicService(session=SimpleNamespace())
        service.repository = _TenantAwareRepository()

        with pytest.raises(NotFoundError):
            await service.update_topic(1, tenant_id=2, name="Blocked")

        with pytest.raises(NotFoundError):
            await service.delete_topic(1, tenant_id=2)

        with pytest.raises(NotFoundError):
            await service.create_question(
                topic_id=1,
                difficulty=1,
                question_type="multiple_choice",
                question_text="Blocked",
                correct_answer="A",
                accepted_answers=[],
                answer_options=["A", "B"],
                tenant_id=2,
            )

    asyncio.run(_run())
