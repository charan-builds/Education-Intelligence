from __future__ import annotations

import inspect
from datetime import datetime, timezone
from types import SimpleNamespace

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import NotFoundError
from app.application.services.diagnostic.expiry_guard import enforce_diagnostic_not_expired
from app.application.services.diagnostic.scoring_service import DiagnosticScoringService
from app.application.services.learning_profile_service import LearningProfileService
from app.core.feature_flags import FeatureFlagService
from app.domain.engines.adaptive_testing_engine import AdaptiveTestingEngine
from app.domain.engines.weakness_modeling_engine import WeaknessModelingEngine
from app.infrastructure.repositories.diagnostic_repository import DiagnosticRepository
from app.infrastructure.repositories.topic_repository import TopicRepository
from app.schemas.question_serializer import sanitize_question


class AdaptiveSelectionService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        diagnostic_repository: DiagnosticRepository | None = None,
        topic_repository: TopicRepository | None = None,
        feature_flag_service: FeatureFlagService | None = None,
        learning_profile_service: LearningProfileService | None = None,
        weakness_engine: WeaknessModelingEngine | None = None,
        adaptive_engine: AdaptiveTestingEngine | None = None,
        scoring_service: DiagnosticScoringService | None = None,
    ):
        self.session = session
        self.diagnostic_repository = diagnostic_repository or DiagnosticRepository(session)
        self.topic_repository = topic_repository or TopicRepository(session)
        self.feature_flag_service = feature_flag_service or FeatureFlagService(session)
        self.learning_profile_service = learning_profile_service or LearningProfileService(session)
        self.weakness_engine = weakness_engine or WeaknessModelingEngine()
        self.adaptive_engine = adaptive_engine or AdaptiveTestingEngine()
        self.scoring_service = scoring_service or DiagnosticScoringService()

    @staticmethod
    def _int_list(values: list | None) -> list[int]:
        return [int(value) for value in (values or []) if isinstance(value, int) or str(value).isdigit()]

    @staticmethod
    def _difficulty_int(question: object) -> int:
        difficulty = getattr(question, "difficulty_level", getattr(question, "difficulty", 2))
        try:
            return int(difficulty)
        except (TypeError, ValueError):
            return {"easy": 1, "medium": 2, "hard": 3}.get(str(difficulty).lower(), 2)

    @classmethod
    def _difficulty_label(cls, question: object) -> str:
        label = getattr(question, "difficulty_label", None)
        if label in {"easy", "medium", "hard"}:
            return str(label)
        return {1: "easy", 2: "medium", 3: "hard"}.get(cls._difficulty_int(question), "medium")

    @classmethod
    def _serialize_question(
        cls,
        *,
        test_id: int,
        question: object,
        adaptive_strategy: str,
        target_topic_id: int | None,
        target_difficulty: int | None,
        weakness_topic_ids: list[int],
    ) -> dict:
        question_type = getattr(question, "question_type", "short_text")
        return sanitize_question({
            "test_id": int(test_id),
            "id": int(getattr(question, "id")),
            "topic_id": int(getattr(question, "topic_id")),
            "difficulty_level": cls._difficulty_int(question),
            "difficulty_label": cls._difficulty_label(question),
            "adaptive_strategy": adaptive_strategy,
            "target_topic_id": target_topic_id,
            "target_difficulty": target_difficulty,
            "weakness_topic_ids": list(weakness_topic_ids),
            "question_type": str(question_type.value if hasattr(question_type, "value") else question_type),
            "question_text": str(getattr(question, "question_text")),
            "answer_options": list(getattr(question, "answer_options", None) or getattr(question, "options", None) or []),
        })

    async def _list_active_questions_by_ids(self, *, tenant_id: int, question_ids: list[int]) -> list[object]:
        method = self.topic_repository.list_questions_by_ids
        kwargs: dict[str, object] = {
            "tenant_id": tenant_id,
            "question_ids": question_ids,
        }
        try:
            signature = inspect.signature(method)
            if "active_only" in signature.parameters:
                kwargs["active_only"] = True
        except (TypeError, ValueError):
            pass
        return await method(**kwargs)

    @staticmethod
    def _active_planned_question_ids(
        *,
        planned_question_ids: list[int],
        answered_question_ids: set[int],
        active_questions_by_id: dict[int, object],
    ) -> list[int]:
        active_ids = set(active_questions_by_id)
        return [
            int(question_id)
            for question_id in planned_question_ids
            if int(question_id) in answered_question_ids or int(question_id) in active_ids
        ]

    async def get_or_build_test_state(
        self,
        *,
        test_id: int,
        user_id: int,
        tenant_id: int,
        for_update: bool = False,
    ):
        state = None
        if hasattr(self.diagnostic_repository, "get_test_state"):
            state = await self.diagnostic_repository.get_test_state(
                test_id=test_id,
                user_id=user_id,
                tenant_id=tenant_id,
                for_update=for_update,
            )
        if state is not None:
            return (
                state,
                self._int_list(state.answered_question_ids),
                list(state.previous_answers or []),
                self._int_list(getattr(state, "planned_question_ids", []) or []),
            )

        test = await self.diagnostic_repository.get_test_for_user(test_id, user_id, tenant_id)
        if test is None:
            raise NotFoundError("Test not found")

        answers = await self.diagnostic_repository.list_answers_for_test(test_id=test.id)
        previous_answers = [
            {
                "question_id": int(answer.question_id),
                "user_answer": answer.user_answer,
                "time_taken": float(answer.time_taken),
                "score": float(answer.score),
            }
            for answer in answers
        ]
        answered_ids = [int(answer["question_id"]) for answer in previous_answers if "question_id" in answer]
        if not hasattr(self.diagnostic_repository, "upsert_test_state"):
            state = SimpleNamespace(
                test_id=test.id,
                tenant_id=tenant_id,
                user_id=user_id,
                goal_id=test.goal_id,
                answered_question_ids=answered_ids,
                previous_answers=previous_answers,
                planned_question_ids=[],
                expected_next_question_id=None,
            )
            return state, answered_ids, previous_answers, []

        state = await self.diagnostic_repository.upsert_test_state(
            test_id=test.id,
            tenant_id=tenant_id,
            user_id=user_id,
            goal_id=test.goal_id,
            answered_question_ids=answered_ids,
            previous_answers=previous_answers,
            planned_question_ids=[],
            expected_next_question_id=None,
            updated_at=datetime.now(timezone.utc),
        )
        return state, answered_ids, previous_answers, []

    async def get_next_question(self, *, test_id: int, user_id: int, tenant_id: int) -> dict | None:
        test = await self.diagnostic_repository.get_test_for_user(test_id, user_id, tenant_id)
        if test is None:
            raise NotFoundError("Test not found")
        if test.completed_at is not None:
            return None
        await enforce_diagnostic_not_expired(
            test,
            diagnostic_repository=self.diagnostic_repository,
            commit=getattr(self.session, "commit", None),
        )

        state, answered_ids, previous_answers, planned_question_ids = await self.get_or_build_test_state(
            test_id=test_id,
            user_id=user_id,
            tenant_id=tenant_id,
        )
        answered_question_ids = {
            *answered_ids,
            *[
                int(answer.get("question_id"))
                for answer in previous_answers
                if answer.get("question_id") is not None
            ],
        }

        if not planned_question_ids:
            questions = await self.topic_repository.list_questions_for_goal(goal_id=test.goal_id, tenant_id=tenant_id)
            planned_question_ids = [int(question.id) for question in questions]

        question = None
        unanswered_planned_question_ids = [
            int(question_id)
            for question_id in planned_question_ids
            if int(question_id) not in answered_question_ids
        ]
        active_unanswered_questions = await self._list_active_questions_by_ids(
            tenant_id=tenant_id,
            question_ids=unanswered_planned_question_ids,
        )
        active_questions_by_id = {int(question.id): question for question in active_unanswered_questions}
        selectable_planned_question_ids = self._active_planned_question_ids(
            planned_question_ids=planned_question_ids,
            answered_question_ids=answered_question_ids,
            active_questions_by_id=active_questions_by_id,
        )
        next_question_id = None
        for question_id in unanswered_planned_question_ids:
            question = active_questions_by_id.get(int(question_id))
            if question is not None:
                next_question_id = int(question_id)
                break

        if next_question_id is None:
            if state.expected_next_question_id is not None or selectable_planned_question_ids != planned_question_ids:
                await self.diagnostic_repository.upsert_test_state(
                    test_id=test.id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    goal_id=test.goal_id,
                    answered_question_ids=sorted(answered_question_ids),
                    previous_answers=previous_answers,
                    planned_question_ids=selectable_planned_question_ids,
                    expected_next_question_id=None,
                    updated_at=datetime.now(timezone.utc),
                )
            return None

        if (
            state.expected_next_question_id != int(next_question_id)
            or selectable_planned_question_ids != planned_question_ids
        ):
            await self.diagnostic_repository.upsert_test_state(
                test_id=test.id,
                tenant_id=tenant_id,
                user_id=user_id,
                goal_id=test.goal_id,
                answered_question_ids=sorted(answered_question_ids),
                previous_answers=previous_answers,
                planned_question_ids=selectable_planned_question_ids,
                expected_next_question_id=int(next_question_id),
                updated_at=datetime.now(timezone.utc),
            )

        return self._serialize_question(
            test_id=test.id,
            question=question,
            adaptive_strategy="planned_batch",
            target_topic_id=None,
            target_difficulty=None,
            weakness_topic_ids=[],
        )

    async def select_next_question(
        self,
        goal_id: int,
        previous_answers: list[dict],
        user_id: int | None = None,
        topic_scores: dict[int, float] | None = None,
        question_ids: list[int] | None = None,
        tenant_id: int | None = None,
    ) -> dict | None:
        if question_ids:
            questions = await self._list_active_questions_by_ids(
                tenant_id=int(tenant_id) if tenant_id is not None else 1,
                question_ids=[int(question_id) for question_id in question_ids],
            )
        else:
            questions = await self.topic_repository.list_questions_for_goal(goal_id=goal_id, tenant_id=tenant_id)

        adaptive_enabled = True
        if tenant_id is not None:
            adaptive_enabled = await self.feature_flag_service.is_enabled(
                "adaptive_testing_enabled",
                tenant_id,
            )

        question_lookup = {int(question.id): question for question in questions}
        scored_previous_answers = self.scoring_service.evaluate_answers(previous_answers, question_lookup)
        weakness_topic_ids: list[int] = []
        if tenant_id is not None and topic_scores:
            prerequisite_map: dict[int, list[int]] = {}
            for topic_id, prerequisite_topic_id in await self.topic_repository.get_prerequisite_edges(tenant_id=tenant_id):
                prerequisite_map.setdefault(int(topic_id), []).append(int(prerequisite_topic_id))
            weakness_analysis = self.weakness_engine.analyze(
                topic_scores={int(topic_id): float(score) for topic_id, score in topic_scores.items()},
                prerequisite_map=prerequisite_map,
            )
            weakness_topic_ids = [int(item["topic_id"]) for item in weakness_analysis["deep_weaknesses"][:4]]

        learning_profile = {}
        if tenant_id is not None and user_id is not None:
            learning_profile = await self.learning_profile_service.get_for_user(
                user_id=int(user_id),
                tenant_id=int(tenant_id),
            )

        next_selection = self.adaptive_engine.select_next_question(
            questions=questions,
            previous_answers=scored_previous_answers,
            topic_scores=topic_scores,
            weakness_topic_ids=weakness_topic_ids,
            feature_flags={"adaptive_testing_enabled": adaptive_enabled},
            learning_profile=learning_profile,
        )
        if next_selection is None:
            return None

        next_question = next_selection.question
        difficulty_level = self._difficulty_int(next_question)
        return sanitize_question({
            "id": int(next_question.id),
            "topic_id": int(next_question.topic_id),
            "difficulty_level": difficulty_level,
            "difficulty_label": {1: "easy", 2: "medium", 3: "hard"}.get(difficulty_level, "medium"),
            "adaptive_strategy": next_selection.strategy,
            "target_topic_id": next_selection.target_topic_id,
            "target_difficulty": next_selection.target_difficulty,
            "weakness_topic_ids": next_selection.weakness_topic_ids,
            "question_type": next_question.question_type,
            "question_text": next_question.question_text,
            "answer_options": list(next_question.answer_options or []),
        })
