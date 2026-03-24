import asyncio
from types import SimpleNamespace

from app.application.services.diagnostic_service import DiagnosticService


class _FeatureFlags:
    async def is_enabled(self, _flag_name: str, _tenant_id: int) -> bool:
        return True


class _TopicRepository:
    async def list_questions_for_goal(self, goal_id: int | None = None):
        _ = goal_id
        return [
            SimpleNamespace(
                id=1,
                topic_id=11,
                difficulty=2,
                question_type="multiple_choice",
                question_text="Which value is correct?",
                correct_answer="B",
                accepted_answers=[],
                answer_options=["A", "B", "C", "D"],
            )
        ]


def test_select_next_question_includes_answer_options():
    async def _run():
        service = DiagnosticService(session=SimpleNamespace())
        service.topic_repository = _TopicRepository()
        service.feature_flag_service = _FeatureFlags()

        question = await service.select_next_question(goal_id=1, previous_answers=[], tenant_id=1)

        assert question is not None
        assert question["question_type"] == "multiple_choice"
        assert question["answer_options"] == ["A", "B", "C", "D"]

    asyncio.run(_run())
