import asyncio
from types import SimpleNamespace

from starlette.requests import Request

from app.presentation import diagnostic_routes
from app.schemas.diagnostic_schema import DiagnosticAnswerRequest, DiagnosticStartRequest, DiagnosticSubmitRequest


class _DummySession:
    async def commit(self):
        return None


class _FakeDiagnosticService:
    last_start = None
    last_answer = None
    last_next = None
    last_submit = None

    def __init__(self, session):
        self.session = session

    async def start_test_with_questions(self, *, user_id: int, goal_id: int, tenant_id: int, question_count: int = 20):
        _FakeDiagnosticService.last_start = (user_id, goal_id, tenant_id, question_count)
        return SimpleNamespace(
            id=55,
            test_id=55,
            user_id=user_id,
            goal_id=goal_id,
            started_at="2026-03-25T00:00:00Z",
            completed_at=None,
            questions=[],
        )

    async def answer_question(self, **kwargs):
        _FakeDiagnosticService.last_answer = kwargs
        return {
            "test_id": kwargs["test_id"],
            "question_id": kwargs["question_id"],
            "answered_count": 2,
            "completed_at": None,
            "adaptive_decision": {
                "mode": "batch",
                "status": "recorded",
                "next_question_id": None,
                "requires_submit": True,
            },
        }

    async def get_next_question(self, **kwargs):
        _FakeDiagnosticService.last_next = kwargs
        return {
            "test_id": kwargs["test_id"],
            "id": 101,
            "topic_id": 3,
            "difficulty_level": 2,
            "difficulty_label": "medium",
            "question_text": "What is a vector?",
            "question_type": "short_text",
            "answer_options": [],
        }

    async def submit_test(self, **kwargs):
        _FakeDiagnosticService.last_submit = kwargs
        return {
            "id": 55,
            "user_id": kwargs["user_id"],
            "goal_id": 9,
            "started_at": "2026-03-25T00:00:00Z",
            "completed_at": "2026-03-25T00:10:00Z",
            "adaptive_summary": {
                "topic_levels": [
                    {
                        "topic_id": 3,
                        "level": "intermediate",
                        "average_accuracy": 0.75,
                        "average_time_taken": 18.0,
                        "average_attempts": 1.0,
                        "recommended_difficulty": 2,
                    }
                ]
            },
        }


def _user():
    return SimpleNamespace(id=7, tenant_id=3, role=SimpleNamespace(value="student"))


def test_server_owned_diagnostic_routes(monkeypatch):
    monkeypatch.setattr(diagnostic_routes, "DiagnosticService", _FakeDiagnosticService)

    request = Request({"type": "http", "method": "POST", "path": "/diagnostic", "headers": []})

    async def _run():
        started = await diagnostic_routes.start_diagnostic(
            request=request,
            payload=DiagnosticStartRequest(goal_id=9),
            db=_DummySession(),
            current_user=_user(),
        )
        assert started.id == 55
        assert _FakeDiagnosticService.last_start == (7, 9, 3, 20)

        next_question = await diagnostic_routes.diagnostic_next_question_for_test(
            test_id=55,
            db=_DummySession(),
            current_user=_user(),
        )
        assert next_question.id == 101
        assert next_question.difficulty_level == 2
        assert next_question.difficulty_label == "medium"
        assert _FakeDiagnosticService.last_next == {"test_id": 55, "user_id": 7, "tenant_id": 3}

        answer = await diagnostic_routes.answer_diagnostic_question(
            request=request,
            payload=DiagnosticAnswerRequest(test_id=55, question_id=101, user_answer="A quantity", time_taken=12),
            db=_DummySession(),
            current_user=_user(),
        )
        assert answer["answered_count"] == 2
        assert _FakeDiagnosticService.last_answer["tenant_id"] == 3
        assert answer["adaptive_decision"]["requires_submit"] is True

        submitted = await diagnostic_routes.submit_diagnostic(
            request=request,
            payload=DiagnosticSubmitRequest(test_id=55),
            db=_DummySession(),
            current_user=_user(),
        )
        assert submitted["completed_at"] is not None
        assert submitted["adaptive_summary"]["topic_levels"][0]["topic_id"] == 3
        assert _FakeDiagnosticService.last_submit == {
            "test_id": 55,
            "user_id": 7,
            "tenant_id": 3,
            "answers": None,
            "trigger_roadmap": True,
        }

    asyncio.run(_run())
