import asyncio

from app.application.services.mentor_service import MentorService


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
