import asyncio
import sys
from types import SimpleNamespace
from types import ModuleType

from starlette.requests import Request

fake_celery = ModuleType("celery")
fake_celery_signals = ModuleType("celery.signals")


class _FakeSignal:
    def connect(self, *_args, **_kwargs):
        return None


class _FakeCelery:
    def __init__(self, *args, **kwargs):
        _ = args, kwargs
        self.conf = SimpleNamespace(update=lambda **kw: None)

    def config_from_object(self, *args, **kwargs):
        _ = args, kwargs

    def send_task(self, *args, **kwargs):
        _ = args, kwargs
        return None

    def autodiscover_tasks(self, *args, **kwargs):
        _ = args, kwargs

    def task(self, *args, **kwargs):
        _ = args, kwargs

        def _decorator(func):
            return func

        return _decorator


fake_celery.Celery = _FakeCelery
fake_celery_signals.before_task_publish = _FakeSignal()
fake_celery_signals.task_failure = _FakeSignal()
fake_celery_signals.task_postrun = _FakeSignal()
fake_celery_signals.task_prerun = _FakeSignal()
fake_celery_signals.task_retry = _FakeSignal()
sys.modules.setdefault("celery", fake_celery)
sys.modules.setdefault("celery.signals", fake_celery_signals)

from app.presentation import mentor_routes
from app.schemas.mentor_schema import MentorChatAckRequest, MentorChatRequest


class _DummySession:
    async def commit(self):
        return None


class _FakeMentorChatRepository:
    stored = {}

    def __init__(self, session):
        self.session = session

    async def upsert_message(self, **kwargs):
        key = (kwargs["tenant_id"], kwargs["user_id"], kwargs["request_id"], kwargs["direction"])
        row = SimpleNamespace(
            request_id=kwargs["request_id"],
            channel=kwargs["channel"],
            status=kwargs["status"],
            content=kwargs["content"],
            delivered_at=None,
            acked_at=None,
        )
        self.stored[key] = row
        return row

    async def mark_delivered(self, row):
        row.status = "delivered"
        row.delivered_at = True
        return row

    async def get_by_request(self, *, tenant_id, user_id, request_id, direction):
        return self.stored.get((tenant_id, user_id, request_id, direction))

    async def mark_acked(self, row):
        row.status = "acked"
        row.acked_at = True
        return row


class _FakeMentorMessageRepository:
    messages = {}

    def __init__(self, session=None):
        self.session = session

    async def create_message(self, **kwargs):
        key = (kwargs["tenant_id"], kwargs["user_id"], kwargs["request_id"], kwargs["role"])
        self.messages[key] = kwargs
        return SimpleNamespace(**kwargs)

    async def set_response(self, *, request_id, response, status):
        # find message by request_id
        for key, saved in self.messages.items():
            if key[2] == request_id:
                saved_data = self.messages[key]
                saved_data["response"] = response
                saved_data["status"] = status
                return SimpleNamespace(**saved_data)
        return None

    async def mark_acked(self, *, request_id):
        for key, saved in self.messages.items():
            if key[2] == request_id:
                saved["status"] = "delivered"
                return SimpleNamespace(**saved)
        return None

    async def get_by_request(self, *, request_id, tenant_id, user_id):
        key = (tenant_id, user_id, request_id, "learner")
        saved_data = self.messages.get(key)
        if saved_data is None:
            return None
        return SimpleNamespace(**saved_data)

    async def mark_delivered(self, row):
        row.status = "delivered"
        row.delivered_at = True
        return row

    async def get_by_request(self, *, tenant_id, user_id, request_id, direction):
        return self.stored.get((tenant_id, user_id, request_id, direction))

    async def mark_acked(self, row):
        row.status = "acked"
        row.acked_at = True
        return row


def _user():
    return SimpleNamespace(id=9, tenant_id=4, role=SimpleNamespace(value="student"))


def test_mentor_chat_route_uses_authenticated_scope(monkeypatch):
    service_calls = []

    class _FakeMentorService:
        def __init__(self, session):
            self.session = session

        async def chat(self, *, message, user_id, tenant_id, chat_history):
            service_calls.append(
                {
                    "message": message,
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "chat_history": chat_history,
                }
            )
            return {
                "reply": "Start with your next roadmap topic.",
                "advisor_type": "RuleBasedAdvisor",
                "used_ai": False,
                "fallback_used": True,
                "fallback_reason": "rule_based_fallback",
                "suggested_focus_topics": [11, 12],
                "why_recommended": ["Weak topics were prioritized first."],
                "provider": None,
                "latency_ms": 12.5,
                "next_checkin_date": None,
                "session_summary": "Immediate mentor guidance returned.",
                "memory_summary": {"learner_summary": "Needs practice"},
            }

    monkeypatch.setattr(mentor_routes, "MentorService", _FakeMentorService)
    request = Request({"type": "http", "method": "POST", "path": "/mentor/chat", "headers": []})

    async def _run():
        response = await mentor_routes.mentor_chat(
            request=request,
            payload=MentorChatRequest(
                message="What should I do next?",
                request_id="req-1",
                chat_history=[],
            ),
            db=_DummySession(),
            current_user=_user(),
        )
        assert response.reply == "Start with your next roadmap topic."
        assert response.request_id == "req-1"
        assert response.status == "ready"
        assert response.advisor_type == "RuleBasedAdvisor"
        assert service_calls == [
            {
                "message": "What should I do next?",
                "user_id": 9,
                "tenant_id": 4,
                "chat_history": [],
            }
        ]

    asyncio.run(_run())


def test_mentor_chat_ack_marks_delivery(monkeypatch):
    call_log = {"chat_repo_acked": False, "msg_repo_acked": False}

    class _TestChatRepo:
        def __init__(self, session=None):
            pass

        async def get_by_request(self, *, tenant_id, user_id, request_id, direction):
            return SimpleNamespace(request_id=request_id, status="delivered", channel="http", content="reply", delivered_at=True, acked_at=False)

        async def mark_acked(self, row):
            call_log["chat_repo_acked"] = True
            row.acked_at = True
            return row

    class _TestMessageRepo:
        def __init__(self, session=None):
            pass

        async def mark_acked(self, *, request_id):
            call_log["msg_repo_acked"] = True
            return None

    monkeypatch.setattr(mentor_routes, "MentorChatRepository", _TestChatRepo)
    monkeypatch.setattr(mentor_routes, "MentorMessageRepository", _TestMessageRepo)

    async def _run():
        response = await mentor_routes.mentor_chat_ack(
            payload=MentorChatAckRequest(request_id="req-ack"),
            db=_DummySession(),
            current_user=_user(),
        )
        assert response.request_id == "req-ack"
        assert response.acked is True
        assert call_log["chat_repo_acked"] is True
        assert call_log["msg_repo_acked"] is True

    asyncio.run(_run())


def test_mentor_suggestions_allows_unmapped_mentor_fallback(monkeypatch):
    class _NoMappingRepo:
        def __init__(self, session=None):
            self.session = session

        async def has_mapping(self, *, tenant_id, mentor_id, student_id):
            _ = tenant_id, mentor_id, student_id
            return False

        async def list_student_ids_for_mentor(self, *, tenant_id, mentor_id):
            _ = tenant_id, mentor_id
            return []

    class _FakeMentorService:
        def __init__(self, session=None):
            self.session = session

        async def contextual_suggestions(self, *, user_id, tenant_id):
            return {
                "suggestions": [f"Focus learner {user_id} in tenant {tenant_id}."],
                "reasons": ["Fallback access path works."],
            }

    monkeypatch.setattr(mentor_routes, "MentorStudentRepository", _NoMappingRepo)
    monkeypatch.setattr(mentor_routes, "MentorService", _FakeMentorService)

    async def _run():
        response = await mentor_routes.mentor_suggestions(
            learner_id=None,
            db=_DummySession(),
            current_user=SimpleNamespace(id=14, tenant_id=4, role=SimpleNamespace(value="mentor")),
        )
        assert response.suggestions == ["Focus learner 14 in tenant 4."]

    asyncio.run(_run())
