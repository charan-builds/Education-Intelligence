from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.feature_flags import FeatureFlagService
from app.domain.engines.adaptive_testing_engine import AdaptiveTestingEngine
from app.domain.engines.weakness_modeling_engine import WeaknessModelingEngine
from app.application.services.learning_event_service import LearningEventService
from app.application.services.ml_platform_service import MLPlatformService
from app.application.services.retention_service import RetentionService
from app.application.services.skill_vector_service import SkillVectorService
from app.infrastructure.repositories.goal_repository import GoalRepository
from app.infrastructure.repositories.diagnostic_repository import DiagnosticRepository
from app.infrastructure.repositories.roadmap_repository import RoadmapRepository
from app.infrastructure.repositories.topic_repository import TopicRepository
from app.application.exceptions import NotFoundError, ValidationError


class DiagnosticService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.diagnostic_repository = DiagnosticRepository(session)
        self.topic_repository = TopicRepository(session)
        self.goal_repository = GoalRepository(session)
        self.roadmap_repository = RoadmapRepository(session)
        self.adaptive_engine = AdaptiveTestingEngine()
        self.weakness_engine = WeaknessModelingEngine()
        self.feature_flag_service = FeatureFlagService(session)
        self.learning_event_service = LearningEventService(session)
        self.retention_service = RetentionService(session)
        self.skill_vector_service = SkillVectorService(session)
        self.ml_platform_service = MLPlatformService(session)

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
            goal = await self.goal_repository.get_by_id(tenant_id=tenant_id, goal_id=goal_id)
            if goal is None:
                raise NotFoundError("Goal not found")
            existing = await self.diagnostic_repository.get_latest_open_test_for_user(
                user_id=user_id,
                goal_id=goal_id,
                tenant_id=tenant_id,
            )
            if existing is not None:
                return existing
            test = await self.diagnostic_repository.create_test(user_id=user_id, goal_id=goal_id, started_at=datetime.now(timezone.utc))
            await self.session.commit()
            return test
        except Exception:
            await self.session.rollback()
            raise

    async def get_or_resume_test(self, *, test_id: int, user_id: int, tenant_id: int):
        test = await self.diagnostic_repository.get_test_for_user(test_id, user_id, tenant_id)
        if test is None:
            raise NotFoundError("Test not found")
        answers = await self.diagnostic_repository.list_answers_for_test(test_id=test.id)
        return test, answers

    async def get_next_question(self, *, test_id: int, user_id: int, tenant_id: int) -> dict | None:
        test, answers = await self.get_or_resume_test(test_id=test_id, user_id=user_id, tenant_id=tenant_id)
        previous_answers = [
            {
                "question_id": answer.question_id,
                "user_answer": answer.user_answer,
                "time_taken": answer.time_taken,
                "score": answer.score,
            }
            for answer in answers
        ]
        question = await self.select_next_question(
            goal_id=test.goal_id,
            previous_answers=previous_answers,
            tenant_id=tenant_id,
        )
        if question is None:
            return None
        return {"test_id": test.id, **question}

    async def answer_question(
        self,
        *,
        test_id: int,
        user_id: int,
        tenant_id: int,
        question_id: int,
        user_answer: str,
        time_taken: float,
    ) -> dict:
        try:
            test = await self.diagnostic_repository.get_test_for_user(
                test_id,
                user_id,
                tenant_id,
                for_update=True,
            )
            if test is None:
                raise NotFoundError("Test not found")
            existing_answers = await self.diagnostic_repository.list_answers_for_test(test_id=test.id)
            if test.completed_at is not None:
                raise ValidationError("Diagnostic test already completed")

            next_question = await self.get_next_question(test_id=test_id, user_id=user_id, tenant_id=tenant_id)
            if next_question is None:
                raise ValidationError("Diagnostic is already complete")
            if int(next_question["id"]) != int(question_id):
                raise ValidationError("Question does not match the expected next diagnostic step")

            question = await self.topic_repository.get_question(question_id, tenant_id)
            if question is None:
                raise NotFoundError(f"Question {question_id} not found")

            score = self._score_answer(
                question.correct_answer,
                user_answer,
                getattr(question, "accepted_answers", []),
            )
            await self.diagnostic_repository.upsert_answer(
                test_id=test_id,
                question_id=question_id,
                user_answer=user_answer,
                score=score,
                time_taken=time_taken,
            )
            await self.learning_event_service.track_question_answered(
                tenant_id=tenant_id,
                user_id=user_id,
                topic_id=question.topic_id,
                diagnostic_test_id=test_id,
                question_id=question.id,
                score=score,
                time_taken=time_taken,
                idempotency_key=f"diagnostic-answer:{tenant_id}:{user_id}:{test_id}:{question.id}",
                commit=False,
            )
            await self.skill_vector_service.update_from_diagnostic_answer(
                tenant_id=tenant_id,
                user_id=user_id,
                topic_id=question.topic_id,
                score=score,
                time_taken_seconds=time_taken,
                answered_at=datetime.now(timezone.utc),
            )
            await self.session.commit()
            return {
                "test_id": test_id,
                "question_id": question_id,
                "answered_count": len(existing_answers) + (0 if any(a.question_id == question_id for a in existing_answers) else 1),
                "completed_at": test.completed_at,
            }
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
            test = await self.diagnostic_repository.get_test_for_user(test_id, user_id, tenant_id, for_update=True)
            if not test:
                raise NotFoundError("Test not found")
            if test.completed_at is not None:
                return test

            question_ids = [int(answer["question_id"]) for answer in answers]
            question_rows = await self.topic_repository.list_questions_by_ids(
                tenant_id=tenant_id,
                question_ids=question_ids,
            )
            questions_by_id = {int(question.id): question for question in question_rows}

            for answer in answers:
                question = questions_by_id.get(int(answer["question_id"]))
                if question is None:
                    raise NotFoundError(f"Question {answer['question_id']} not found")
                existing_answer = await self.diagnostic_repository.get_answer_for_test_question(
                    test_id=test_id,
                    question_id=answer["question_id"],
                    for_update=True,
                )
                score = self._score_answer(
                    question.correct_answer,
                    answer["user_answer"],
                    getattr(question, "accepted_answers", []),
                )
                await self.diagnostic_repository.upsert_answer(
                    test_id=test_id,
                    question_id=answer["question_id"],
                    user_answer=answer["user_answer"],
                    score=score,
                    time_taken=answer["time_taken"],
                )
                if existing_answer is None:
                    await self.learning_event_service.track_question_answered(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        topic_id=question.topic_id,
                        diagnostic_test_id=test_id,
                        question_id=question.id,
                        score=score,
                        time_taken=answer["time_taken"],
                        idempotency_key=f"diagnostic-answer:{tenant_id}:{user_id}:{test_id}:{question.id}",
                        commit=False,
                    )
                    await self.skill_vector_service.update_from_diagnostic_answer(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        topic_id=question.topic_id,
                        score=score,
                        time_taken_seconds=answer["time_taken"],
                        answered_at=datetime.now(timezone.utc),
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
                idempotency_key=f"diagnostic-complete:{tenant_id}:{user_id}:{test_id}",
                commit=False,
            )
            await self.session.commit()
            await self.ml_platform_service.build_feature_snapshot(user_id=user_id, tenant_id=tenant_id)
            return test
        except Exception:
            await self.session.rollback()
            raise

    async def finalize_test(self, *, test_id: int, user_id: int, tenant_id: int):
        test, answers = await self.get_or_resume_test(test_id=test_id, user_id=user_id, tenant_id=tenant_id)
        if test.completed_at is not None:
            return test
        next_question = await self.get_next_question(test_id=test_id, user_id=user_id, tenant_id=tenant_id)
        if next_question is not None:
            raise ValidationError("Diagnostic still has unanswered questions")
        return await self.submit_answers(
            test_id=test_id,
            user_id=user_id,
            tenant_id=tenant_id,
            answers=[
                {
                    "question_id": answer.question_id,
                    "user_answer": answer.user_answer,
                    "time_taken": answer.time_taken,
                }
                for answer in answers
            ],
        )

    async def get_result(self, test_id: int, user_id: int, tenant_id: int) -> dict:
        scores = await self.diagnostic_repository.topic_scores_for_test(test_id, user_id, tenant_id)
        test = await self.diagnostic_repository.get_test_for_user(test_id, user_id, tenant_id)
        if not test:
            raise NotFoundError("Test not found")
        roadmap = await self.roadmap_repository.get_by_identity(
            user_id=user_id,
            goal_id=test.goal_id,
            test_id=test_id,
            tenant_id=tenant_id,
        )
        return {
            "test_id": test_id,
            "topic_scores": scores,
            "roadmap": roadmap,
        }

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
