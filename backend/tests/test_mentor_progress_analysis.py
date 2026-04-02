import asyncio

from app.application.services.mentor_service import MentorService


def test_progress_analysis_without_session_returns_defaults():
    async def _run():
        service = MentorService()
        result = await service.progress_analysis(user_id=1)
        assert "topic_improvements" in result
        assert "weekly_progress" in result
        assert "recommended_focus" in result
        assert isinstance(result["recommended_focus"], list)

    asyncio.run(_run())
