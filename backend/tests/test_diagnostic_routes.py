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
    last_finalize = None

    def __init__(self, session):
        self.session = session

    async def start_test(self, user_id: int, goal_id: int, tenant_id: int):
        _FakeDiagnosticService.last_start = (user_id, goal_id, tenant_id)
        return SimpleNamespace(id=55, user_id=user_id, goal_id=goal_id, started_at="2026-03-25T00:00:00Z", completed_at=None)

    async def answer_question(self, **kwargs):
        _FakeDiagnosticService.last_answer = kwargs
        return {
            "test_id": kwargs["test_id"],
            "question_id": kwargs["question_id"],
            "answered_count": 2,
            "completed_at": None,
            "adaptive_decision": {
                "topic_id": 3,
                "current_difficulty": 2,
                "recommended_difficulty": 3,
                "accuracy": 1.0,
                "time_taken": 12.0,
                "attempt_count": 1,
                "level": "advanced",
                "rule": "increase_difficulty",
            },
        }

    async def get_next_question(self, **kwargs):
        _FakeDiagnosticService.last_next = kwargs
        return {
            "test_id": kwargs["test_id"],
            "id": 101,
            "topic_id": 3,
            "difficulty": 2,
            "difficulty_label": "medium",
            "question_text": "What is a vector?",
            "question_type": "short_text",
            "answer_options": [],
        }

    async def finalize_test(self, **kwargs):
        _FakeDiagnosticService.last_finalize = kwargs
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


class _FakeRoadmapService:
    last_request = None

    def __init__(self, session):
        self.session = session

    async def ensure_generation_requested(self, **kwargs):
        _FakeRoadmapService.last_request = kwargs
        return None, True


class _FakeOutboxService:
    last_event = None

    def __init__(self, session):
        self.session = session

    async def add_task_event(self, **kwargs):
        _FakeOutboxService.last_event = kwargs
        return None


def _user():
    return SimpleNamespace(id=7, tenant_id=3, role=SimpleNamespace(value="student"))


def test_server_owned_diagnostic_routes(monkeypatch):
    monkeypatch.setattr(diagnostic_routes, "DiagnosticService", _FakeDiagnosticService)
    monkeypatch.setattr(diagnostic_routes, "RoadmapService", _FakeRoadmapService)
    monkeypatch.setattr(diagnostic_routes, "OutboxService", _FakeOutboxService)

    request = Request({"type": "http", "method": "POST", "path": "/diagnostic", "headers": []})

    async def _run():
        started = await diagnostic_routes.start_diagnostic(
            request=request,
            payload=DiagnosticStartRequest(goal_id=9),
            db=_DummySession(),
            current_user=_user(),
        )
        assert started.id == 55
        assert _FakeDiagnosticService.last_start == (7, 9, 3)

        next_question = await diagnostic_routes.diagnostic_next_question_for_test(
            test_id=55,
            db=_DummySession(),
            current_user=_user(),
        )
        assert next_question.id == 101
        assert _FakeDiagnosticService.last_next == {"test_id": 55, "user_id": 7, "tenant_id": 3}

        answer = await diagnostic_routes.answer_diagnostic_question(
            request=request,
            payload=DiagnosticAnswerRequest(test_id=55, question_id=101, user_answer="A quantity", time_taken=12),
            db=_DummySession(),
            current_user=_user(),
        )
        assert answer["answered_count"] == 2
        assert _FakeDiagnosticService.last_answer["tenant_id"] == 3
        assert answer["adaptive_decision"]["recommended_difficulty"] == 3

        submitted = await diagnostic_routes.submit_diagnostic(
            request=request,
            payload=DiagnosticSubmitRequest(test_id=55),
            db=_DummySession(),
            current_user=_user(),
        )
        assert submitted["completed_at"] is not None
        assert submitted["adaptive_summary"]["topic_levels"][0]["topic_id"] == 3
        assert _FakeDiagnosticService.last_finalize == {"test_id": 55, "user_id": 7, "tenant_id": 3}
        assert _FakeRoadmapService.last_request["test_id"] == 55
        assert _FakeOutboxService.last_event["task_name"] == "jobs.generate_roadmap"

    asyncio.run(_run())
