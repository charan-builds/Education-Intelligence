from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.feature_flags import FeatureFlagService
from app.domain.engines.adaptive_testing_engine import AdaptiveTestingEngine
from app.domain.engines.weakness_modeling_engine import WeaknessModelingEngine
from app.application.services.learning_event_service import LearningEventService
from app.application.services.retention_service import RetentionService
from app.infrastructure.repositories.goal_repository import GoalRepository
from app.infrastructure.repositories.diagnostic_repository import DiagnosticRepository
from app.infrastructure.repositories.topic_repository import TopicRepository
from app.application.exceptions import NotFoundError


class DiagnosticService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.diagnostic_repository = DiagnosticRepository(session)
        self.topic_repository = TopicRepository(session)
        self.goal_repository = GoalRepository(session)
        self.adaptive_engine = AdaptiveTestingEngine()
        self.weakness_engine = WeaknessModelingEngine()
        self.feature_flag_service = FeatureFlagService(session)
        self.learning_event_service = LearningEventService(session)
        self.retention_service = RetentionService(session)

    @staticmethod
    def _normalize_answer(value: str) -> str:
        return "".join(ch.lower() for ch in value.strip() if ch.isalnum() or ch.isspace()).strip()

    def _score_answer(self, expected_answer: str, user_answer: str, accepted_answers: list[str] | None = None) -> float:
        normalized_expected = self._normalize_answer(expected_answer)
        normalized_user = self._normalize_answer(user_answer)
        if not normalized_expected or not normalized_user:
            return 0.0
        valid_answers = {normalized_expected}
        for alias in accepted_answers or []:
            normalized_alias = self._normalize_answer(alias)
            if normalized_alias:
                valid_answers.add(normalized_alias)
        return 100.0 if normalized_user in valid_answers else 0.0

    async def start_test(self, user_id: int, goal_id: int, tenant_id: int = 1):
        try:
            test = await self.diagnostic_repository.create_test(
                user_id=user_id,
                goal_id=goal_id,
                started_at=datetime.now(timezone.utc),
            )
            await self.session.commit()
            return test
        except Exception:
            await self.session.rollback()
            raise

    async def submit_answers(
        self,
        test_id: int,
        user_id: int,
        tenant_id: int,
        answers: list[dict],
    ):
        try:
            test = await self.diagnostic_repository.get_test_for_user(test_id, user_id, tenant_id)
            if not test:
                raise NotFoundError("Test not found")

            for answer in answers:
                question = await self.topic_repository.get_question(answer["question_id"])
                if question is None:
                    raise NotFoundError(f"Question {answer['question_id']} not found")
                score = self._score_answer(
                    question.correct_answer,
                    answer["user_answer"],
                    getattr(question, "accepted_answers", []),
                )
                await self.diagnostic_repository.add_answer(
                    test_id=test_id,
                    question_id=answer["question_id"],
                    user_answer=answer["user_answer"],
                    score=score,
                    time_taken=answer["time_taken"],
                )
                await self.learning_event_service.track_question_answered(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    topic_id=question.topic_id,
                    diagnostic_test_id=test_id,
                    question_id=question.id,
                    score=score,
                    time_taken=answer["time_taken"],
                    commit=False,
                )

            await self.diagnostic_repository.complete_test(test, datetime.now(timezone.utc))
            topic_scores = await self.diagnostic_repository.topic_scores_for_test(test_id, user_id, tenant_id)
            for topic_id, topic_score in topic_scores.items():
                await self.retention_service.upsert_topic_score(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    topic_id=int(topic_id),
                    score=float(topic_score),
                    diagnostic_test_id=test_id,
                    confidence=0.75,
                )
            await self.learning_event_service.track_diagnostic_completed(
                tenant_id=tenant_id,
                user_id=user_id,
                diagnostic_test_id=test_id,
                goal_id=test.goal_id,
                commit=False,
            )
            await self.session.commit()
            return test
        except Exception:
            await self.session.rollback()
            raise

    async def get_result(self, test_id: int, user_id: int, tenant_id: int) -> dict[int, float]:
        return await self.diagnostic_repository.topic_scores_for_test(test_id, user_id, tenant_id)

    async def select_next_question(
        self,
        goal_id: int,
        previous_answers: list[dict],
        topic_scores: dict[int, float] | None = None,
        tenant_id: int | None = None,
    ) -> dict | None:
        questions = await self.topic_repository.list_questions_for_goal(goal_id=goal_id, tenant_id=tenant_id)
        adaptive_enabled = True
        if tenant_id is not None:
            adaptive_enabled = await self.feature_flag_service.is_enabled(
                "adaptive_testing_enabled",
                tenant_id,
            )

        question_lookup = {question.id: question for question in questions}
        scored_previous_answers: list[dict] = []
        for answer in previous_answers:
            question = question_lookup.get(int(answer["question_id"]))
            if question is None:
                continue
            scored_previous_answers.append(
                {
                    **answer,
                    "score": self._score_answer(
                        question.correct_answer,
                        str(answer["user_answer"]),
                        getattr(question, "accepted_answers", []),
                    ),
                }
            )
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

        next_selection = self.adaptive_engine.select_next_question(
            questions=questions,
            previous_answers=scored_previous_answers,
            topic_scores=topic_scores,
            weakness_topic_ids=weakness_topic_ids,
            feature_flags={"adaptive_testing_enabled": adaptive_enabled},
        )
        if next_selection is None:
            return None
        next_question = next_selection.question
        return {
            "id": next_question.id,
            "topic_id": next_question.topic_id,
            "difficulty": next_question.difficulty,
            "difficulty_label": {1: "easy", 2: "medium", 3: "hard"}.get(next_question.difficulty, "medium"),
            "adaptive_strategy": next_selection.strategy,
            "target_topic_id": next_selection.target_topic_id,
            "target_difficulty": next_selection.target_difficulty,
            "weakness_topic_ids": next_selection.weakness_topic_ids,
            "question_type": next_question.question_type,
            "question_text": next_question.question_text,
            "answer_options": list(next_question.answer_options or []),
        }
