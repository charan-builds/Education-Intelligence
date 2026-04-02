import asyncio
from types import SimpleNamespace

from app.presentation import ai_routes
from app.schemas.ai_schema import AIChatRequest


class _FakeAIChatService:
    last_chat = None
    last_history = None

    def __init__(self, session):
        self.session = session

    async def history(self, *, tenant_id: int, user_id: int, limit: int = 20):
        _FakeAIChatService.last_history = {"tenant_id": tenant_id, "user_id": user_id, "limit": limit}
        return [
            {
                "request_id": "ai-1",
                "role": "learner",
                "message": "Explain joins",
                "response": "A join combines rows from related tables.",
                "status": "sent",
                "created_at": "2026-03-29T00:00:00Z",
            }
        ]

    async def chat(self, *, tenant_id: int, user_id: int, message: str, chat_history: list[dict[str, str]] | None = None):
        _FakeAIChatService.last_chat = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "message": message,
            "chat_history": chat_history,
        }
        return {
            "request_id": "ai-2",
            "reply": "Focus on joins next, then move to aggregations.",
            "advisor_type": "AIServiceClient",
            "used_ai": True,
            "suggested_focus_topics": [12, 13],
            "why_recommended": ["These topics are next on the roadmap."],
            "provider": "mock-ai",
            "next_checkin_date": None,
            "session_summary": "Roadmap-aware next-step guidance.",
            "memory_summary": {},
            "prompt_context": {
                "system_role": "AI mentor",
                "goal": "Explain topics and suggest next actions.",
            },
            "history": [],
        }


def _user():
    return SimpleNamespace(id=7, tenant_id=3)


def test_ai_chat_history_route(monkeypatch):
    monkeypatch.setattr(ai_routes, "AIChatService", _FakeAIChatService)

    async def _run():
        result = await ai_routes.ai_chat_history(db=object(), current_user=_user())
        assert result[0]["request_id"] == "ai-1"
        assert _FakeAIChatService.last_history == {"tenant_id": 3, "user_id": 7, "limit": 20}

    asyncio.run(_run())


def test_ai_chat_route(monkeypatch):
    monkeypatch.setattr(ai_routes, "AIChatService", _FakeAIChatService)

    async def _run():
        result = await ai_routes.ai_chat(
            payload=AIChatRequest(
                message="What topic should I study next?",
                chat_history=[{"role": "user", "content": "I finished arrays."}],
            ),
            db=object(),
            current_user=_user(),
        )
        assert result["request_id"] == "ai-2"
        assert result["suggested_focus_topics"] == [12, 13]
        assert _FakeAIChatService.last_chat == {
            "tenant_id": 3,
            "user_id": 7,
            "message": "What topic should I study next?",
            "chat_history": [{"role": "user", "content": "I finished arrays."}],
        }

    asyncio.run(_run())
