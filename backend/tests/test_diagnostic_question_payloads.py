import asyncio
from datetime import datetime, timezone
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

    async def list_questions_by_ids(self, *, tenant_id: int, question_ids: list[int], active_only: bool = False):
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
                is_active=True,
            )
            for question_id in question_ids
        ]

    async def get_question(self, question_id: int, tenant_id: int | None = None, active_only: bool = False):
        _ = tenant_id, active_only
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


def _open_test(test_id: int, user_id: int):
    return SimpleNamespace(
        id=test_id,
        user_id=user_id,
        goal_id=9,
        started_at=datetime.now(timezone.utc),
        test_duration=20,
        completed_at=None,
        expired_at=None,
    )


def test_get_next_question_uses_planned_question_ids_from_state():
    async def _run():
        service = DiagnosticService(session=SimpleNamespace())
        service.topic_repository = _TopicRepository()
        service.feature_flag_service = _FeatureFlags()
        service.diagnostic_repository = SimpleNamespace(
            get_test_for_user=lambda test_id, user_id, tenant_id: _async_return(
                _open_test(test_id, user_id)
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


def test_get_next_question_skips_inactive_planned_question_ids():
    class _TopicRepositoryWithInactive(_TopicRepository):
        inactive_question_ids = {9}

        async def list_questions_by_ids(self, *, tenant_id: int, question_ids: list[int], active_only: bool = False):
            questions = await super().list_questions_by_ids(
                tenant_id=tenant_id,
                question_ids=question_ids,
                active_only=active_only,
            )
            if active_only:
                return [question for question in questions if question.id not in self.inactive_question_ids]
            return questions

    async def _run():
        service = DiagnosticService(session=SimpleNamespace())
        service.topic_repository = _TopicRepositoryWithInactive()
        service.feature_flag_service = _FeatureFlags()
        persisted_updates: list[dict] = []
        service.diagnostic_repository = SimpleNamespace(
            get_test_for_user=lambda test_id, user_id, tenant_id: _async_return(
                _open_test(test_id, user_id)
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
            upsert_test_state=lambda **kwargs: persisted_updates.append(kwargs) or _async_return(SimpleNamespace(**kwargs)),
        )

        question = await service.get_next_question(test_id=55, user_id=7, tenant_id=1)

        assert question is not None
        assert question["id"] == 5
        assert persisted_updates[-1]["expected_next_question_id"] == 5
        assert persisted_updates[-1]["planned_question_ids"] == [5, 7]

    asyncio.run(_run())


def test_get_next_question_stops_when_state_has_max_answers():
    async def _run():
        service = DiagnosticService(session=SimpleNamespace())
        service.topic_repository = _TopicRepository()
        service.feature_flag_service = _FeatureFlags()
        persisted_updates: list[dict] = []
        max_answers = [
            {
                "question_id": index + 1,
                "score": 100.0,
                "time_taken": 10.0,
                "accuracy": 1.0,
                "attempt_count": 1,
            }
            for index in range(service.adaptive_engine.MAX_QUESTIONS)
        ]
        service.diagnostic_repository = SimpleNamespace(
            get_test_for_user=lambda test_id, user_id, tenant_id: _async_return(
                _open_test(test_id, user_id)
            ),
            get_test_state=lambda **kwargs: _async_return(
                SimpleNamespace(
                    test_id=55,
                    tenant_id=1,
                    user_id=7,
                    goal_id=9,
                    answered_question_ids=[item["question_id"] for item in max_answers],
                    previous_answers=max_answers,
                    planned_question_ids=[],
                    expected_next_question_id=99,
                )
            ),
            upsert_test_state=lambda **kwargs: persisted_updates.append(kwargs) or _async_return(SimpleNamespace(**kwargs)),
        )

        question = await service.get_next_question(test_id=55, user_id=7, tenant_id=1)

        assert question is None
        assert persisted_updates
        assert persisted_updates[-1]["expected_next_question_id"] is None

    asyncio.run(_run())
