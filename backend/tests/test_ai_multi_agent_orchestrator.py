import asyncio

import pytest

pytest.importorskip("openai")

from ai_service.config import AISettings
from ai_service.schemas import MentorResponseRequest
from ai_service.service import AIOrchestrator


def test_route_agents_includes_specialists_for_career_and_progress_signals():
    orchestrator = AIOrchestrator(AISettings())
    payload = MentorResponseRequest(
        user_id=1,
        tenant_id=1,
        message="Help me improve my progress and prepare for interviews",
        weak_topics=[11, 12],
        mentor_context={"roadmap_progress": {"completion_rate": 35.0}},
    )

    routed = orchestrator._route_agents(payload)

    assert "mentor_agent" in routed
    assert "analytics_agent" in routed
    assert "career_advisor_agent" in routed
    assert "motivation_agent" in routed


def test_mentor_chat_fallback_returns_multi_agent_metadata():
    async def _run():
        orchestrator = AIOrchestrator(AISettings())
        payload = MentorResponseRequest(
            user_id=5,
            tenant_id=2,
            message="Explain what I should do next and keep me motivated",
            weak_topics=[7],
            learning_profile={"profile_type": "practice_focused"},
            mentor_context={
                "roadmap_progress": {"completion_rate": 22.0},
                "weak_topics": [{"topic_id": 7, "topic_name": "Graph Theory"}],
                "strong_topics": [{"topic_id": 9, "topic_name": "Python"}],
                "user_profile": {"learning_speed": 18.0},
            },
        )

        result = await orchestrator.mentor_chat(payload)

        assert result.routed_agents
        assert result.orchestrator_summary
        assert len(result.agent_outputs) >= 2
        assert "mentor_agent" in result.routed_agents
        assert any(item.agent_name == "motivation_agent" for item in result.agent_outputs)
        assert result.fallback_used is True

    asyncio.run(_run())
