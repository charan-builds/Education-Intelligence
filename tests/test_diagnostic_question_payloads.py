import asyncio
from types import SimpleNamespace

from app.application.services.diagnostic_service import DiagnosticService


class _FeatureFlags:
    async def is_enabled(self, _flag_name: str, _tenant_id: int) -> bool:
        return True


class _TopicRepository:
    async def list_questions_for_goal(self, goal_id: int | None = None, tenant_id: int | None = None):
        _ = goal_id, tenant_id
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

    async def list_questions_by_ids(self, *, tenant_id: int, question_ids: list[int]):
        _ = tenant_id
        return [
            SimpleNamespace(
                id=question_id,
                topic_id=11,
                difficulty=2,
                question_type="multiple_choice",
                question_text=f"Question {question_id}",
                correct_answer="B",
                accepted_answers=[],
                answer_options=["A", "B", "C", "D"],
            )
            for question_id in question_ids
        ]

    async def get_question(self, question_id: int, tenant_id: int | None = None):
        _ = tenant_id
        return SimpleNamespace(
            id=question_id,
            topic_id=11,
            difficulty=2,
            question_type="multiple_choice",
            question_text=f"Question {question_id}",
            answer_options=["A", "B", "C", "D"],
        )


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


async def _async_return(value):
    return value


def test_get_next_question_uses_planned_question_ids_from_state():
    async def _run():
        service = DiagnosticService(session=SimpleNamespace())
        service.topic_repository = _TopicRepository()
        service.feature_flag_service = _FeatureFlags()
        service.diagnostic_repository = SimpleNamespace(
            get_test_for_user=lambda test_id, user_id, tenant_id: _async_return(
                SimpleNamespace(id=test_id, user_id=user_id, goal_id=9, completed_at=None)
            ),
            get_test_state=lambda **kwargs: _async_return(
                SimpleNamespace(
                    test_id=55,
                    tenant_id=1,
                    user_id=7,
                    goal_id=9,
                    answered_question_ids=[],
                    previous_answers=[],
                    planned_question_ids=[9, 5, 7],
                    expected_next_question_id=9,
                )
            ),
        )

        question = await service.get_next_question(test_id=55, user_id=7, tenant_id=1)

        assert question is not None
        assert question["id"] == 9
        assert question["question_text"] == "Question 9"

    asyncio.run(_run())
