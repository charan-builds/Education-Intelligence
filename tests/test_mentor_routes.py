import asyncio
from types import SimpleNamespace

from starlette.requests import Request

from app.presentation import mentor_routes
from app.schemas.mentor_schema import MentorChatAckRequest, MentorChatRequest


class _DummySession:
    async def commit(self):
        return None


class _FakeMentorService:
    last_chat = None

    def __init__(self, session):
        self.session = session

    async def chat(self, **kwargs):
        _FakeMentorService.last_chat = kwargs
        return {
            "reply": "Focus on the next roadmap step.",
            "advisor_type": "RuleBasedMentorAdvisor",
            "used_ai": False,
            "fallback_used": False,
            "fallback_reason": None,
            "suggested_focus_topics": [3],
            "why_recommended": ["Your roadmap is partially complete."],
            "provider": None,
            "latency_ms": None,
            "next_checkin_date": None,
            "session_summary": "Re-centered the learner on the next milestone.",
            "memory_summary": {},
        }


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
    monkeypatch.setattr(mentor_routes, "MentorService", _FakeMentorService)
    monkeypatch.setattr(mentor_routes, "MentorChatRepository", _FakeMentorChatRepository)
    monkeypatch.setattr(mentor_routes, "MentorMessageRepository", _FakeMentorMessageRepository)
    monkeypatch.setattr(
        mentor_routes,
        "realtime_hub",
        SimpleNamespace(send_user=lambda *args, **kwargs: asyncio.sleep(0)),
    )
    request = Request({"type": "http", "method": "POST", "path": "/mentor/chat", "headers": []})

    async def _run():
        response = await mentor_routes.mentor_chat(
            request=request,
            payload=MentorChatRequest(
                user_id=9,
                tenant_id=4,
                message="What should I do next?",
                request_id="req-1",
                chat_history=[],
            ),
            db=_DummySession(),
            current_user=_user(),
        )
        assert response.reply == "Focus on the next roadmap step."
        assert response.request_id == "req-1"
        assert _FakeMentorService.last_chat["tenant_id"] == 4
        assert _FakeMentorService.last_chat["user_id"] == 9

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
