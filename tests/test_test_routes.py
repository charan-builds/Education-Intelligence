import asyncio
from types import SimpleNamespace

from app.presentation import test_routes
from app.schemas.test_generation_schema import SmartTestGenerateRequest


class _FakeTestGeneratorService:
    last_call = None

    def __init__(self, session):
        self.session = session

    async def generate_smart_test(self, **kwargs):
        _FakeTestGeneratorService.last_call = kwargs
        return {
            "tenant_id": kwargs["tenant_id"],
            "user_id": kwargs["user_id"],
            "goal_id": kwargs["goal_id"],
            "test_id": 55,
            "started_at": "2026-03-29T00:00:00Z",
            "next_question_id": 102,
            "persisted_session": True,
            "question_count": 3,
            "generated_from_weak_topics": [
                {
                    "topic_id": 11,
                    "topic_name": "SQL Basics",
                    "mastery_score": 32.0,
                    "confidence": 0.35,
                    "target_difficulty": 1,
                    "selected_question_count": 2,
                }
            ],
            "difficulty_mix": {"easy": 1, "medium": 1, "hard": 1},
            "repeated_question_count": 0,
            "questions": [
                {
                    "id": 102,
                    "topic_id": 11,
                    "topic_name": "SQL Basics",
                    "difficulty": 1,
                    "difficulty_label": "easy",
                    "question_type": "multiple_choice",
                    "question_text": "What is SQL?",
                    "answer_options": ["A", "B"],
                }
            ],
        }


def test_generate_smart_test_route(monkeypatch):
    monkeypatch.setattr(test_routes, "SmartTestGeneratorService", _FakeTestGeneratorService)

    async def _run():
        response = await test_routes.generate_smart_test(
            payload=SmartTestGenerateRequest(goal_id=9, question_count=6),
            db=object(),
            current_user=SimpleNamespace(id=7, tenant_id=3),
        )
        assert response["test_id"] == 55
        assert response["persisted_session"] is True
        assert response["question_count"] == 3
        assert response["generated_from_weak_topics"][0]["topic_id"] == 11
        assert _FakeTestGeneratorService.last_call == {
            "tenant_id": 3,
            "user_id": 7,
            "goal_id": 9,
            "question_count": 6,
        }

    asyncio.run(_run())
