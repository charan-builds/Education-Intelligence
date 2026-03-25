import asyncio
from types import SimpleNamespace

from starlette.requests import Request

from app.presentation import mentor_routes
from app.schemas.mentor_schema import MentorChatRequest


class _DummySession:
    pass


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


def _user():
    return SimpleNamespace(id=9, tenant_id=4, role=SimpleNamespace(value="student"))


def test_mentor_chat_route_uses_authenticated_scope(monkeypatch):
    monkeypatch.setattr(mentor_routes, "MentorService", _FakeMentorService)
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
        assert _FakeMentorService.last_chat["tenant_id"] == 4
        assert _FakeMentorService.last_chat["user_id"] == 9

    asyncio.run(_run())
