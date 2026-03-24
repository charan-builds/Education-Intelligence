import asyncio
from types import SimpleNamespace

from app.application.services.mentor_service import LearnerMentorContext, MentorService


def test_generate_advice_without_session_uses_fallback_text():
    async def _run():
        service = MentorService()
        text = await service.generate_advice(user_id=1, message="How should I improve?")
        assert "Focus on one weak topic" in text
        assert "How should I improve?" in text

    asyncio.run(_run())


def test_generate_advice_without_message_prompts_for_question():
    async def _run():
        service = MentorService()
        text = await service.generate_advice(user_id=1, message="   ")
        assert "Please share your learning question" in text

    asyncio.run(_run())


def test_chat_uses_ai_when_feature_flag_enabled():
    async def _run():
        service = MentorService()

        async def fake_is_enabled(_feature_name: str, _tenant_id: int) -> bool:
            return True

        async def fake_load_user_context(*, user_id: int, tenant_id: int | None = None):
            assert user_id == 7
            assert tenant_id == 3
            return LearnerMentorContext(
                tenant_id=3,
                steps=[],
                completed_steps=1,
                completion_rate=50.0,
                overdue_steps=0,
                topic_scores={11: 52.0},
                learning_profile={"profile_type": "practice_focused", "confidence": 0.9},
                missing_foundations=[11],
            )

        async def fake_ai_response(**_kwargs):
            return {
                "reply": "AI says focus on topic 11 this week.",
                "suggested_focus_topics": [11],
                "next_checkin_date": "2026-03-25",
            }

        service.feature_flag_service = SimpleNamespace(is_enabled=fake_is_enabled)
        service._load_user_context = fake_load_user_context  # type: ignore[method-assign]
        service._try_ai_mentor_response = fake_ai_response  # type: ignore[method-assign]

        result = await service.chat(message="How do I catch up?", user_id=7, tenant_id=3)

        assert result["used_ai"] is True
        assert result["advisor_type"] == "AIServiceClient"
        assert result["reply"] == "AI says focus on topic 11 this week."
        assert result["suggested_focus_topics"] == [11]

    asyncio.run(_run())


def test_chat_returns_memory_summary_when_ai_memory_updates_are_available():
    async def _run():
        service = MentorService()

        async def fake_is_enabled(_feature_name: str, _tenant_id: int) -> bool:
            return True

        async def fake_load_user_context(*, user_id: int, tenant_id: int | None = None):
            return LearnerMentorContext(
                tenant_id=3,
                steps=[],
                completed_steps=2,
                completion_rate=66.0,
                overdue_steps=0,
                topic_scores={11: 52.0, 12: 88.0},
                learning_profile={"profile_type": "practice_focused", "confidence": 0.9},
                missing_foundations=[11],
            )

        async def fake_build_mentor_context(**_kwargs):
            return {"user_profile": {"learning_speed": 18.0}}

        async def fake_update_after_session(**_kwargs):
            return SimpleNamespace(
                learner_summary="Learner improves with short drill-based sessions.",
                preferred_learning_style="practice_focused",
                learning_speed=18.0,
                weak_topics=["Topic 11"],
                strong_topics=["Topic 12"],
                past_mistakes=["Confuses core Topic 11 concepts"],
                improvement_signals=["Recovered one prior weak topic"],
                last_session_summary="Reviewed Topic 11 with targeted coaching.",
            )

        async def fake_ai_response(**_kwargs):
            return {
                "reply": "AI says focus on topic 11 this week.",
                "suggested_focus_topics": [11],
                "next_checkin_date": "2026-03-25",
                "session_summary": "Reviewed Topic 11 with targeted coaching.",
                "memory_update": {"preferred_learning_style": "practice_focused"},
            }

        service.feature_flag_service = SimpleNamespace(is_enabled=fake_is_enabled)
        service._load_user_context = fake_load_user_context  # type: ignore[method-assign]
        service._try_ai_mentor_response = fake_ai_response  # type: ignore[method-assign]
        service.ai_context_builder = SimpleNamespace(
            build_mentor_context=fake_build_mentor_context,
            memory_service=SimpleNamespace(update_after_session=fake_update_after_session),
        )

        result = await service.chat(message="Help me improve.", user_id=7, tenant_id=3)

        assert result["used_ai"] is True
        assert result["session_summary"] == "Reviewed Topic 11 with targeted coaching."
        assert result["memory_summary"]["preferred_learning_style"] == "practice_focused"
        assert result["memory_summary"]["weak_topics_history"] == ["Topic 11"]

    asyncio.run(_run())
