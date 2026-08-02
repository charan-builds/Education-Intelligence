import asyncio
from types import SimpleNamespace

from starlette.requests import Request

from app.presentation import diagnostic_routes, topic_routes
from app.schemas.common_schema import PaginationParams
from app.schemas.diagnostic_schema import DiagnosticStartRequest, DiagnosticSubmitRequest
from app.schemas.question_serializer import sanitize_question


class _Session:
    pass


def _user(role: str = "student"):
    return SimpleNamespace(id=7, tenant_id=3, role=SimpleNamespace(value=role))


def _assert_no_answer_metadata(value):
    if isinstance(value, dict):
        assert "correct_answer" not in value
        assert "accepted_answers" not in value
        assert "explanation" not in value
        assert "is_correct" not in value
        for item in value.values():
            _assert_no_answer_metadata(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_answer_metadata(item)


def test_sanitize_question_strips_answer_metadata_without_mutating_source():
    question = {
        "id": 1,
        "topic_id": 2,
        "difficulty": 1,
        "question_type": "multiple_choice",
        "question_text": "Choose the correct option",
        "correct_answer": "B",
        "accepted_answers": ["B"],
        "explanation": "B is correct",
        "options": [
            {"key": "A", "text": "Alpha", "is_correct": False},
            {"key": "B", "text": "Beta", "is_correct": True},
        ],
    }

    sanitized = sanitize_question(question)

    assert sanitized["difficulty_level"] == 1
    assert sanitized["difficulty_label"] == "easy"
    assert sanitized["options"] == [
        {"key": "A", "text": "Alpha"},
        {"key": "B", "text": "Beta"},
    ]
    _assert_no_answer_metadata(sanitized)
    assert question["options"][1]["is_correct"] is True


def test_diagnostic_start_route_sanitizes_questions(monkeypatch):
    class _DiagnosticService:
        def __init__(self, session):
            self.session = session

        async def start_test_with_questions(self, **kwargs):
            return {
                "id": 55,
                "test_id": 55,
                "user_id": kwargs["user_id"],
                "goal_id": kwargs["goal_id"],
                "started_at": "2026-03-25T00:00:00Z",
                "completed_at": None,
                "questions": [
                    {
                        "id": 1,
                        "topic_id": 2,
                        "difficulty": "medium",
                        "question_type": "multiple_choice",
                        "question_text": "Which option?",
                        "correct_answer": "B",
                        "explanation": "B is correct",
                        "options": [
                            {"key": "A", "text": "Alpha", "is_correct": False},
                            {"key": "B", "text": "Beta", "is_correct": True},
                        ],
                    }
                ],
            }

    monkeypatch.setattr(diagnostic_routes, "DiagnosticService", _DiagnosticService)
    request = Request({"type": "http", "method": "POST", "path": "/diagnostic/start", "headers": []})

    async def _run():
        response = await diagnostic_routes.start_diagnostic(
            request=request,
            payload=DiagnosticStartRequest(goal_id=9),
            db=_Session(),
            current_user=_user(),
        )
        payload = response.model_dump()
        _assert_no_answer_metadata(payload)
        assert "difficulty" not in payload["questions"][0]
        assert payload["questions"][0]["difficulty_level"] == 2
        assert payload["questions"][0]["difficulty_label"] == "medium"
        assert payload["questions"][0]["options"] == [
            {"key": "A", "text": "Alpha"},
            {"key": "B", "text": "Beta"},
        ]

    asyncio.run(_run())


def test_diagnostic_submit_route_does_not_return_is_correct(monkeypatch):
    class _DiagnosticService:
        def __init__(self, session):
            self.session = session

        async def submit_test(self, **kwargs):
            return {
                "id": 55,
                "test_id": 55,
                "user_id": kwargs["user_id"],
                "goal_id": 9,
                "started_at": "2026-03-25T00:00:00Z",
                "completed_at": "2026-03-25T00:10:00Z",
                "adaptive_summary": {"topic_levels": []},
                "answers": [
                    {
                        "question_id": 1,
                        "selected_answer": "B",
                        "is_correct": True,
                        "score": 100.0,
                        "time_taken": 9.0,
                        "difficulty_level": 1,
                        "difficulty_label": "easy",
                    }
                ],
            }

    monkeypatch.setattr(diagnostic_routes, "DiagnosticService", _DiagnosticService)
    request = Request({"type": "http", "method": "POST", "path": "/diagnostic/submit", "headers": []})

    async def _run():
        response = await diagnostic_routes.submit_diagnostic(
            request=request,
            payload=DiagnosticSubmitRequest(test_id=55),
            db=_Session(),
            current_user=_user(),
        )
        payload = response
        _assert_no_answer_metadata(payload)
        assert payload["answers"] == [
            {
                "question_id": 1,
                "selected_answer": "B",
                "score": 100.0,
                "time_taken": 9.0,
                "difficulty_level": 1,
                "difficulty_label": "easy",
            }
        ]

    asyncio.run(_run())


def test_topic_question_routes_sanitize_list_response(monkeypatch):
    class _TopicService:
        def __init__(self, session):
            self.session = session

        async def list_questions_page(self, **kwargs):
            return {
                "items": [
                    {
                        "id": 1,
                        "topic_id": 2,
                        "difficulty": 1,
                        "question_type": "multiple_choice",
                        "question_text": "Which option?",
                        "correct_answer": "A",
                        "accepted_answers": ["A"],
                        "answer_options": ["Alpha", "Beta"],
                        "options": [
                            {"key": "A", "text": "Alpha", "is_correct": True},
                            {"key": "B", "text": "Beta", "is_correct": False},
                        ],
                    }
                ],
                "meta": {
                    "total": 1,
                    "limit": kwargs["limit"],
                    "offset": kwargs["offset"],
                    "next_offset": None,
                    "next_cursor": None,
                },
            }

    monkeypatch.setattr(topic_routes, "TopicService", _TopicService)

    async def _run():
        response = await topic_routes.list_questions(
            db=_Session(),
            _current_user=_user(),
            pagination=PaginationParams(limit=10, offset=0, cursor=None),
        )
        _assert_no_answer_metadata(response)
        assert response["items"][0]["options"] == [
            {"key": "A", "text": "Alpha"},
            {"key": "B", "text": "Beta"},
        ]

    asyncio.run(_run())
