import asyncio

import pytest

from app.application.services.ai_execution_service import AIExecutionService
from app.application.services.mentor_ai_service import MentorAIService


def test_ai_execution_service_rejects_unknown_request_type():
    service = AIExecutionService()

    async def _run():
        with pytest.raises(ValueError, match="Unsupported AI request type"):
            await service.execute(request_type="unknown", payload={}, tenant_id=1, user_id=2)

    asyncio.run(_run())


def test_ai_execution_service_uses_topic_explanation_executor(monkeypatch):
    class _FakeClient:
        async def explain_topic(self, *, topic_name: str) -> dict:
            return {"topic_name": topic_name, "explanation": "stub"}

    service = AIExecutionService(ai_service_client=_FakeClient())

    async def _run():
        result = await service.execute(
            request_type="topic_explanation",
            payload={"topic_name": "joins"},
            tenant_id=1,
            user_id=2,
        )
        assert result == {"topic_name": "joins", "explanation": "stub"}

    asyncio.run(_run())


def test_ai_execution_service_uses_injected_mentor_ai_service():
    class _FakeMentorAIService:
        async def generate_response(self, **kwargs):  # noqa: ANN003
            return {"reply": "stub", "payload": kwargs}

    service = AIExecutionService(mentor_ai_service=_FakeMentorAIService())

    async def _run():
        result = await service.execute(
            request_type="mentor_chat",
            payload={"message": "help", "weak_topics": [101], "chat_history": []},
            tenant_id=1,
            user_id=2,
            steps=[],
        )
        assert result["reply"] == "stub"
        assert result["payload"]["message"] == "help"
        assert result["payload"]["tenant_id"] == 1
        assert result["payload"]["user_id"] == 2

    asyncio.run(_run())


def test_mentor_ai_service_reuses_injected_client():
    calls: list[dict] = []

    class _FakeClient:
        async def mentor_response(self, **kwargs):  # noqa: ANN003
            calls.append(kwargs)
            return {"response": "mentor reply", "provider": "fake", "latency_ms": 12}

    service = MentorAIService(ai_service_client=_FakeClient())

    async def _run():
        result = await service.generate_response(
            user_id=7,
            tenant_id=3,
            goal="sql",
            message="How do joins work?",
            steps=[],
            weak_topics=[11],
            learning_profile={"pace": "steady"},
            mentor_context={"tone": "encouraging"},
            chat_history=[],
        )
        assert result["reply"] == "mentor reply"
        assert calls and calls[0]["tenant_id"] == 3
        assert calls[0]["user_id"] == 7

    asyncio.run(_run())
