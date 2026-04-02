import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, Response

from app.application.exceptions import NotFoundError, ValidationError
from app.presentation import topic_routes
from app.schemas.common_schema import PaginationParams
from app.schemas.topic_schema import (
    QuestionCreateRequest,
    QuestionImportRequest,
    QuestionUpdateRequest,
    TopicCreateRequest,
    TopicPrerequisiteCreateRequest,
    TopicUpdateRequest,
)


class _DummySession:
    pass


class _FakeTopicService:
    last_list_args = None
    last_topics_args = None
    last_create_payload = None
    last_update_args = None
    last_delete_id = None
    last_import_items = None
    last_export_topic_id = None
    last_csv_import_content = None
    last_create_topic = None
    last_update_topic = None
    last_delete_topic_id = None
    last_prerequisite_create = None
    last_prerequisite_delete_id = None

    def __init__(self, session):
        self.session = session

    async def list_questions_page(self, *, limit: int, offset: int, topic_id: int | None = None):
        _FakeTopicService.last_list_args = {
            "limit": limit,
            "offset": offset,
            "topic_id": topic_id,
            "question_type": None,
            "search": None,
        }
        return {
            "items": [
                {
                    "id": 1,
                    "topic_id": topic_id or 10,
                    "difficulty": 2,
                    "question_type": "multiple_choice",
                    "question_text": "What is 2 + 2?",
                    "correct_answer": "4",
                    "accepted_answers": ["four"],
                    "answer_options": ["3", "4", "5"],
                }
            ],
            "meta": {
                "total": 1,
                "limit": limit,
                "offset": offset,
                "next_offset": None,
                "next_cursor": None,
            },
        }

    async def list_questions_page(
        self,
        *,
        limit: int,
        offset: int,
        topic_id: int | None = None,
        question_type: str | None = None,
        search: str | None = None,
    ):
        _FakeTopicService.last_list_args = {
            "limit": limit,
            "offset": offset,
            "topic_id": topic_id,
            "question_type": question_type,
            "search": search,
        }
        return {
            "items": [
                {
                    "id": 1,
                    "topic_id": topic_id or 10,
                    "difficulty": 2,
                    "question_type": question_type or "multiple_choice",
                    "question_text": "What is 2 + 2?",
                    "correct_answer": "4",
                    "accepted_answers": ["four"],
                    "answer_options": ["3", "4", "5"],
                }
            ],
            "meta": {
                "total": 1,
                "limit": limit,
                "offset": offset,
                "next_offset": None,
                "next_cursor": None,
            },
        }

    async def list_topics_page(self, *, limit: int, offset: int, tenant_id: int):
        _FakeTopicService.last_topics_args = {
            "limit": limit,
            "offset": offset,
            "tenant_id": tenant_id,
        }
        return {
            "items": [
                {"id": 1, "name": "Linear Algebra", "description": "Vectors"},
                {"id": 2, "name": "Statistics", "description": "Probability"},
            ],
            "meta": {
                "total": 2,
                "limit": limit,
                "offset": offset,
                "next_offset": None,
                "next_cursor": None,
            },
        }

    async def create_topic(self, *, name: str, description: str):
        _FakeTopicService.last_create_topic = {"name": name, "description": description}
        return SimpleNamespace(id=5, name=name, description=description)

    async def update_topic(self, topic_id: int, *, name: str | None = None, description: str | None = None):
        _FakeTopicService.last_update_topic = {
            "topic_id": topic_id,
            "name": name,
            "description": description,
        }
        return SimpleNamespace(id=topic_id, name=name or "Existing", description=description or "Updated")

    async def delete_topic(self, topic_id: int):
        _FakeTopicService.last_delete_topic_id = topic_id

    async def list_prerequisites_page(self, *, limit: int, offset: int, topic_id: int | None = None):
        return {
            "items": [{"id": 3, "topic_id": topic_id or 2, "prerequisite_topic_id": 1}],
            "meta": {
                "total": 1,
                "limit": limit,
                "offset": offset,
                "next_offset": None,
                "next_cursor": None,
            },
        }

    async def create_prerequisite(self, *, topic_id: int, prerequisite_topic_id: int):
        _FakeTopicService.last_prerequisite_create = {
            "topic_id": topic_id,
            "prerequisite_topic_id": prerequisite_topic_id,
        }
        return SimpleNamespace(id=9, topic_id=topic_id, prerequisite_topic_id=prerequisite_topic_id)

    async def delete_prerequisite(self, prerequisite_id: int):
        _FakeTopicService.last_prerequisite_delete_id = prerequisite_id

    async def create_question(self, **payload):
        _FakeTopicService.last_create_payload = payload
        return SimpleNamespace(id=2, **payload)

    async def update_question(self, question_id: int, **updates):
        _FakeTopicService.last_update_args = {
            "question_id": question_id,
            "updates": updates,
        }
        return SimpleNamespace(
            id=question_id,
            topic_id=1,
            difficulty=updates.get("difficulty", 2),
            question_type=updates.get("question_type", "multiple_choice"),
            question_text=updates.get("question_text", "Updated"),
            correct_answer=updates.get("correct_answer", "4"),
            accepted_answers=updates.get("accepted_answers", ["four"]),
            answer_options=updates.get("answer_options", ["3", "4", "5"]),
        )

    async def delete_question(self, question_id: int) -> None:
        _FakeTopicService.last_delete_id = question_id

    async def import_questions(self, items: list[dict]):
        _FakeTopicService.last_import_items = items
        return len(items)

    async def export_questions(self, topic_id: int | None = None):
        _FakeTopicService.last_export_topic_id = topic_id
        return [{"id": 1, "topic_id": topic_id or 10, "question_text": "Exported"}]

    async def import_questions_csv(self, content: str):
        _FakeTopicService.last_csv_import_content = content
        return 2

    async def export_questions_csv(self, topic_id: int | None = None):
        _FakeTopicService.last_export_topic_id = topic_id
        return "topic_id,question_text\n10,Exported\n"


def _user(role: str, tenant_id: int = 10):
    return SimpleNamespace(role=SimpleNamespace(value=role), tenant_id=tenant_id)


def test_list_questions_route_passthrough(monkeypatch):
    monkeypatch.setattr(topic_routes, "TopicService", _FakeTopicService)

    async def _run():
        result = await topic_routes.list_questions(
            topic_id=7,
            question_type="multiple_choice",
            search="algebra",
            db=_DummySession(),
            _current_user=_user("student"),
            pagination=PaginationParams(limit=5, offset=10, cursor=None),
        )
        assert result["meta"]["total"] == 1
        assert _FakeTopicService.last_list_args == {
            "limit": 5,
            "offset": 10,
            "topic_id": 7,
            "question_type": "multiple_choice",
            "search": "algebra",
        }

    asyncio.run(_run())


def test_list_topics_route_passthrough(monkeypatch):
    monkeypatch.setattr(topic_routes, "TopicService", _FakeTopicService)

    async def _run():
        result = await topic_routes.list_topics(
            db=_DummySession(),
            current_user=_user("student", tenant_id=7),
            pagination=PaginationParams(limit=5, offset=0, cursor=None),
        )
        assert result["meta"]["total"] == 2
        assert _FakeTopicService.last_topics_args == {
            "limit": 5,
            "offset": 0,
            "tenant_id": 7,
        }

    asyncio.run(_run())


def test_create_topic_admin(monkeypatch):
    monkeypatch.setattr(topic_routes, "TopicService", _FakeTopicService)

    async def _run():
        result = await topic_routes.create_topic(
            payload=TopicCreateRequest(name="New Topic", description="Foundations"),
            db=_DummySession(),
            _current_user=_user("admin"),
        )
        assert result.id == 5
        assert _FakeTopicService.last_create_topic == {
            "name": "New Topic",
            "description": "Foundations",
        }

    asyncio.run(_run())


def test_update_topic_admin(monkeypatch):
    monkeypatch.setattr(topic_routes, "TopicService", _FakeTopicService)

    async def _run():
        result = await topic_routes.update_topic(
            topic_id=7,
            payload=TopicUpdateRequest(name="Renamed Topic"),
            db=_DummySession(),
            _current_user=_user("admin"),
        )
        assert result.id == 7
        assert _FakeTopicService.last_update_topic == {
            "topic_id": 7,
            "name": "Renamed Topic",
            "description": None,
        }

    asyncio.run(_run())


def test_delete_topic_admin(monkeypatch):
    monkeypatch.setattr(topic_routes, "TopicService", _FakeTopicService)

    async def _run():
        result = await topic_routes.delete_topic(
            topic_id=12,
            db=_DummySession(),
            _current_user=_user("admin"),
        )
        assert isinstance(result, Response)
        assert result.status_code == 204
        assert _FakeTopicService.last_delete_topic_id == 12

    asyncio.run(_run())


def test_list_prerequisites_route(monkeypatch):
    monkeypatch.setattr(topic_routes, "TopicService", _FakeTopicService)

    async def _run():
        result = await topic_routes.list_prerequisites(
            topic_id=2,
            db=_DummySession(),
            _current_user=_user("teacher"),
            pagination=PaginationParams(limit=10, offset=0, cursor=None),
        )
        assert result["items"][0]["prerequisite_topic_id"] == 1

    asyncio.run(_run())


def test_create_prerequisite_admin(monkeypatch):
    monkeypatch.setattr(topic_routes, "TopicService", _FakeTopicService)

    async def _run():
        result = await topic_routes.create_prerequisite(
            payload=TopicPrerequisiteCreateRequest(topic_id=2, prerequisite_topic_id=1),
            db=_DummySession(),
            _current_user=_user("admin"),
        )
        assert result.id == 9
        assert _FakeTopicService.last_prerequisite_create == {
            "topic_id": 2,
            "prerequisite_topic_id": 1,
        }

    asyncio.run(_run())


def test_delete_prerequisite_admin(monkeypatch):
    monkeypatch.setattr(topic_routes, "TopicService", _FakeTopicService)

    async def _run():
        result = await topic_routes.delete_prerequisite(
            prerequisite_id=9,
            db=_DummySession(),
            _current_user=_user("admin"),
        )
        assert isinstance(result, Response)
        assert result.status_code == 204
        assert _FakeTopicService.last_prerequisite_delete_id == 9

    asyncio.run(_run())


def test_create_question_admin(monkeypatch):
    monkeypatch.setattr(topic_routes, "TopicService", _FakeTopicService)

    async def _run():
        payload = QuestionCreateRequest(
            topic_id=1,
            difficulty=2,
            question_type="multiple_choice",
            question_text="What is 2 + 2?",
            correct_answer="4",
            accepted_answers=["four"],
            answer_options=["3", "4", "5"],
        )
        result = await topic_routes.create_question(
            payload=payload,
            db=_DummySession(),
            _current_user=_user("admin"),
        )
        assert result.id == 2
        assert _FakeTopicService.last_create_payload["question_type"] == "multiple_choice"

    asyncio.run(_run())


def test_update_question_admin(monkeypatch):
    monkeypatch.setattr(topic_routes, "TopicService", _FakeTopicService)

    async def _run():
        payload = QuestionUpdateRequest(
            question_text="Updated question",
            answer_options=["A", "B"],
        )
        result = await topic_routes.update_question(
            question_id=11,
            payload=payload,
            db=_DummySession(),
            _current_user=_user("admin"),
        )
        assert result.id == 11
        assert _FakeTopicService.last_update_args == {
            "question_id": 11,
            "updates": {
                "difficulty": None,
                "question_type": None,
                "question_text": "Updated question",
                "correct_answer": None,
                "accepted_answers": None,
                "answer_options": ["A", "B"],
            },
        }

    asyncio.run(_run())


def test_delete_question_admin(monkeypatch):
    monkeypatch.setattr(topic_routes, "TopicService", _FakeTopicService)

    async def _run():
        result = await topic_routes.delete_question(
            question_id=15,
            db=_DummySession(),
            _current_user=_user("admin"),
        )
        assert isinstance(result, Response)
        assert result.status_code == 204
        assert _FakeTopicService.last_delete_id == 15

    asyncio.run(_run())


def test_create_question_validation_error(monkeypatch):
    class _ValidationTopicService(_FakeTopicService):
        async def create_question(self, **payload):
            _ = payload
            raise ValidationError("multiple_choice questions require non-empty answer_options")

    monkeypatch.setattr(topic_routes, "TopicService", _ValidationTopicService)

    async def _run():
        with pytest.raises(ValidationError):
            await topic_routes.create_question(
                payload=QuestionCreateRequest(
                    topic_id=1,
                    difficulty=1,
                    question_type="multiple_choice",
                    question_text="Question?",
                    correct_answer="A",
                    accepted_answers=[],
                    answer_options=[],
                ),
                db=_DummySession(),
                _current_user=_user("admin"),
            )

    asyncio.run(_run())


def test_update_question_not_found(monkeypatch):
    class _NotFoundTopicService(_FakeTopicService):
        async def update_question(self, question_id: int, **updates):
            _ = question_id, updates
            raise NotFoundError("Question not found")

    monkeypatch.setattr(topic_routes, "TopicService", _NotFoundTopicService)

    async def _run():
        with pytest.raises(NotFoundError):
            await topic_routes.update_question(
                question_id=404,
                payload=QuestionUpdateRequest(question_text="Missing"),
                db=_DummySession(),
                _current_user=_user("admin"),
            )

    asyncio.run(_run())


def test_import_questions_admin(monkeypatch):
    monkeypatch.setattr(topic_routes, "TopicService", _FakeTopicService)

    async def _run():
        result = await topic_routes.import_questions(
            payload=QuestionImportRequest(
                items=[
                    {
                        "topic_id": 1,
                        "difficulty": 1,
                        "question_type": "multiple_choice",
                        "question_text": "Imported?",
                        "correct_answer": "A",
                        "accepted_answers": [],
                        "answer_options": ["A", "B"],
                    }
                ]
            ),
            db=_DummySession(),
            _current_user=_user("admin"),
        )
        assert result.created == 1
        assert len(_FakeTopicService.last_import_items) == 1

    asyncio.run(_run())


def test_export_questions_route(monkeypatch):
    monkeypatch.setattr(topic_routes, "TopicService", _FakeTopicService)

    async def _run():
        result = await topic_routes.export_questions(
            topic_id=8,
            db=_DummySession(),
            _current_user=_user("teacher"),
        )
        assert "Exported" in result.body.decode()
        assert _FakeTopicService.last_export_topic_id == 8

    asyncio.run(_run())


def test_import_questions_csv_route(monkeypatch):
    monkeypatch.setattr(topic_routes, "TopicService", _FakeTopicService)

    async def _run():
        result = await topic_routes.import_questions_csv(
            content="topic_id,difficulty,question_type,question_text,correct_answer,accepted_answers,answer_options\n"
            "1,1,multiple_choice,Imported?,A,,A|B\n",
            db=_DummySession(),
            _current_user=_user("admin"),
        )
        assert result.created == 2
        assert "Imported?" in _FakeTopicService.last_csv_import_content

    asyncio.run(_run())


def test_export_questions_csv_route(monkeypatch):
    monkeypatch.setattr(topic_routes, "TopicService", _FakeTopicService)

    async def _run():
        result = await topic_routes.export_questions_csv(
            topic_id=8,
            db=_DummySession(),
            _current_user=_user("teacher"),
        )
        assert "topic_id,question_text" in result.body.decode()
        assert _FakeTopicService.last_export_topic_id == 8

    asyncio.run(_run())


def test_topic_routes_propagate_not_found_for_foreign_tenant(monkeypatch):
    class _ForeignTenantTopicService(_FakeTopicService):
        async def update_topic(self, topic_id: int, *, name: str | None = None, description: str | None = None):
            _ = topic_id, name, description
            raise NotFoundError("Topic not found")

        async def delete_topic(self, topic_id: int):
            _ = topic_id
            raise NotFoundError("Topic not found")

        async def create_question(self, **payload):
            _ = payload
            raise NotFoundError("Topic not found")

    monkeypatch.setattr(topic_routes, "TopicService", _ForeignTenantTopicService)

    async def _run():
        for action in (
            topic_routes.update_topic(
                topic_id=99,
                payload=TopicUpdateRequest(name="Blocked"),
                db=_DummySession(),
                _current_user=_user("admin"),
            ),
            topic_routes.delete_topic(
                topic_id=99,
                db=_DummySession(),
                _current_user=_user("admin"),
            ),
            topic_routes.create_question(
                payload=QuestionCreateRequest(
                    topic_id=99,
                    difficulty=1,
                    question_type="multiple_choice",
                    question_text="Blocked?",
                    correct_answer="A",
                    accepted_answers=[],
                    answer_options=["A", "B"],
                ),
                db=_DummySession(),
                _current_user=_user("admin"),
            ),
        ):
            try:
                await action
                assert False, "Expected NotFoundError"
            except NotFoundError as exc:
                assert "Topic not found" in str(exc)

    asyncio.run(_run())
