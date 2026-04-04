from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.feature_flags import FeatureFlagService
from app.application.services.adaptive_engine_service import AdaptiveEngineService
from app.application.services.gamification_service import GamificationService
from app.domain.engines.adaptive_testing_engine import AdaptiveTestingEngine
from app.domain.engines.weakness_modeling_engine import WeaknessModelingEngine
from app.application.services.learning_event_service import LearningEventService
from app.application.services.ml_platform_service import MLPlatformService
from app.application.services.outbox_service import OutboxService
from app.application.services.retention_service import RetentionService
from app.application.services.skill_vector_service import SkillVectorService
from app.domain.models.diagnostic_test import DiagnosticTest
from app.application.services.recommendation_service import RecommendationService
from app.infrastructure.cache.cache_service import CacheService
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
        self.adaptive_engine_service = AdaptiveEngineService()
        self.weakness_engine = WeaknessModelingEngine()
        self.feature_flag_service = FeatureFlagService(session)
        self.learning_event_service = LearningEventService(session)
        self.outbox_service = OutboxService(session)
        self.gamification_service = GamificationService(session)
        self.retention_service = RetentionService(session)
        self.skill_vector_service = SkillVectorService(session)
        self.ml_platform_service = MLPlatformService(session)
        self.cache_service = CacheService()
        self.recommendation_service = RecommendationService(session)

    def _score_answer(self, expected_answer: str, user_answer: str, accepted_answers: list[str] | None = None) -> float:
        evaluated = DiagnosticTest.evaluate_answers(
            [{"question_id": 0, "user_answer": user_answer}],
            {
                0: type(
                    "_Question",
                    (),
                    {
                        "correct_answer": expected_answer,
                        "accepted_answers": list(accepted_answers or []),
                    },
                )()
            },
        )
        return float(evaluated[0]["score"]) if evaluated else 0.0

    @staticmethod
    def _accuracy_from_score(score: float) -> float:
        return DiagnosticTest.accuracy_from_score(score)

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
        except IntegrityError:
            await self.session.rollback()
            existing = await self.diagnostic_repository.get_latest_open_test_for_user(
                user_id=user_id,
                goal_id=goal_id,
                tenant_id=tenant_id,
            )
            if existing is not None:
                return existing
            raise
        except Exception:
            await self.session.rollback()
            raise

    async def get_or_resume_test(self, *, test_id: int, user_id: int, tenant_id: int):
        test = await self.diagnostic_repository.get_test_for_user(test_id, user_id, tenant_id)
        if test is None:
            raise NotFoundError("Test not found")
        answers = await self.diagnostic_repository.list_answers_for_test(test_id=test.id)
        return test, answers

    async def _get_or_build_test_state(self, *, test_id: int, user_id: int, tenant_id: int, for_update: bool = False):
        state = await self.diagnostic_repository.get_test_state(
            test_id=test_id,
            user_id=user_id,
            tenant_id=tenant_id,
            for_update=for_update,
        )
        if state is not None:
            answered_ids = [int(x) for x in (state.answered_question_ids or []) if isinstance(x, int) or str(x).isdigit()]
            previous_answers = list(state.previous_answers or [])
            planned_question_ids = [int(x) for x in (getattr(state, "planned_question_ids", []) or []) if isinstance(x, int) or str(x).isdigit()]
            return state, answered_ids, previous_answers, planned_question_ids

        test, answers = await self.get_or_resume_test(test_id=test_id, user_id=user_id, tenant_id=tenant_id)
        previous_answers = [
            {
                "question_id": int(answer.question_id),
                "user_answer": answer.user_answer,
                "time_taken": float(answer.time_taken),
                "score": float(answer.score),
            }
            for answer in answers
        ]
        answered_ids = [int(a["question_id"]) for a in previous_answers if "question_id" in a]
        next_question = await self.select_next_question(
            goal_id=test.goal_id,
            previous_answers=previous_answers,
            tenant_id=tenant_id,
        )
        expected_next_question_id = int(next_question["id"]) if next_question is not None else None
        now = datetime.now(timezone.utc)
        state = await self.diagnostic_repository.upsert_test_state(
            test_id=test.id,
            tenant_id=tenant_id,
            user_id=user_id,
            goal_id=test.goal_id,
            answered_question_ids=answered_ids,
            previous_answers=previous_answers,
            expected_next_question_id=expected_next_question_id,
            updated_at=now,
        )
        return state, answered_ids, previous_answers, []

    async def get_next_question(self, *, test_id: int, user_id: int, tenant_id: int) -> dict | None:
        test = await self.diagnostic_repository.get_test_for_user(test_id, user_id, tenant_id)
        if test is None:
            raise NotFoundError("Test not found")
        if test.completed_at is not None:
            return None

        state, _, previous_answers, planned_question_ids = await self._get_or_build_test_state(test_id=test_id, user_id=user_id, tenant_id=tenant_id)
        if len(previous_answers) >= self.adaptive_engine.MAX_QUESTIONS:
            if state.expected_next_question_id is not None:
                await self.diagnostic_repository.upsert_test_state(
                    test_id=test.id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    goal_id=test.goal_id,
                    answered_question_ids=[int(a.get("question_id")) for a in previous_answers if a.get("question_id") is not None],
                    previous_answers=previous_answers,
                    expected_next_question_id=None,
                    updated_at=datetime.now(timezone.utc),
                )
            return None
        if state.expected_next_question_id is not None:
            question_id = int(state.expected_next_question_id)
            question = await self.topic_repository.get_question(question_id, tenant_id)
            if question is None:
                # If content changed, recompute from persisted history.
                next_question = await self.select_next_question(
                    goal_id=test.goal_id,
                    previous_answers=previous_answers,
                    question_ids=planned_question_ids or None,
                    tenant_id=tenant_id,
                )
                if next_question is None:
                    return None
                await self.diagnostic_repository.upsert_test_state(
                    test_id=test.id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    goal_id=test.goal_id,
                    answered_question_ids=[int(a.get("question_id")) for a in previous_answers if a.get("question_id") is not None],
                    previous_answers=previous_answers,
                    expected_next_question_id=int(next_question["id"]),
                    updated_at=datetime.now(timezone.utc),
                )
                return {"test_id": test.id, **next_question}
            return {
                "test_id": test.id,
                "id": question.id,
                "topic_id": question.topic_id,
                "difficulty": question.difficulty,
                "difficulty_label": {1: "easy", 2: "medium", 3: "hard"}.get(question.difficulty, "medium"),
                "adaptive_strategy": "cached_state",
                "target_topic_id": None,
                "target_difficulty": None,
                "weakness_topic_ids": [],
                "question_type": question.question_type,
                "question_text": question.question_text,
                "answer_options": list(question.answer_options or []),
            }

        next_question = await self.select_next_question(
            goal_id=test.goal_id,
            previous_answers=previous_answers,
            question_ids=planned_question_ids or None,
            tenant_id=tenant_id,
        )
        if next_question is None:
            return None
        await self.diagnostic_repository.upsert_test_state(
            test_id=test.id,
            tenant_id=tenant_id,
            user_id=user_id,
            goal_id=test.goal_id,
            answered_question_ids=[int(a.get("question_id")) for a in previous_answers if a.get("question_id") is not None],
            previous_answers=previous_answers,
            expected_next_question_id=int(next_question["id"]),
            updated_at=datetime.now(timezone.utc),
        )
        return {"test_id": test.id, **next_question}

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
            if test.completed_at is not None:
                raise ValidationError("Diagnostic test already completed")

            state, answered_ids, previous_answers, planned_question_ids = await self._get_or_build_test_state(
                test_id=test.id,
                user_id=user_id,
                tenant_id=tenant_id,
                for_update=True,
            )
            expected = state.expected_next_question_id
            if expected is None:
                computed = await self.select_next_question(
                    goal_id=test.goal_id,
                    previous_answers=previous_answers,
                    question_ids=planned_question_ids or None,
                    tenant_id=tenant_id,
                )
                expected = int(computed["id"]) if computed is not None else None
            if expected is None:
                raise ValidationError("Diagnostic is already complete")
            if int(expected) != int(question_id):
                raise ValidationError("Question does not match the expected next diagnostic step")

            question = await self.topic_repository.get_question(question_id, tenant_id)
            if question is None:
                raise NotFoundError(f"Question {question_id} not found")

            existing_answer = await self.diagnostic_repository.get_answer_for_test_question(
                test_id=test_id,
                question_id=question_id,
                for_update=True,
            )
            attempt_count = int(getattr(existing_answer, "attempt_count", 0) or 0) + 1
            evaluated_answer = DiagnosticTest.evaluate_answers(
                [{"question_id": int(question_id), "user_answer": user_answer, "attempt_count": attempt_count}],
                {int(question.id): question},
            )[0]
            score = float(evaluated_answer["score"])
            accuracy = float(evaluated_answer["accuracy"])
            await self.diagnostic_repository.upsert_answer(
                test_id=test_id,
                question_id=question_id,
                user_answer=user_answer,
                score=score,
                time_taken=time_taken,
                accuracy=accuracy,
                attempt_count=attempt_count,
            )
            adaptive_decision = self.adaptive_engine_service.evaluate_answer(
                topic_id=int(question.topic_id),
                current_difficulty=int(question.difficulty),
                score=score,
                time_taken=time_taken,
                attempt_count=attempt_count,
            )
            # Persist diagnostic state for fast resume/selection.
            normalized_previous: list[dict] = []
            replaced = False
            for item in previous_answers:
                try:
                    if int(item.get("question_id")) == int(question_id):
                        normalized_previous.append(
                            {
                                "question_id": int(question_id),
                                "user_answer": user_answer,
                                "time_taken": float(time_taken),
                                "score": float(score),
                                "accuracy": accuracy,
                                "attempt_count": attempt_count,
                            }
                        )
                        replaced = True
                    else:
                        normalized_previous.append(item)
                except Exception:
                    continue
            if not replaced:
                normalized_previous.append(
                    {
                        "question_id": int(question_id),
                        "user_answer": user_answer,
                        "time_taken": float(time_taken),
                        "score": float(score),
                        "accuracy": accuracy,
                        "attempt_count": attempt_count,
                    }
                )
            new_answered_ids = sorted({*answered_ids, int(question_id)})
            next_after = await self.select_next_question(
                goal_id=test.goal_id,
                previous_answers=normalized_previous,
                question_ids=planned_question_ids or None,
                tenant_id=tenant_id,
            )
            expected_next_question_id = int(next_after["id"]) if next_after is not None else None
            await self.diagnostic_repository.upsert_test_state(
                test_id=test.id,
                tenant_id=tenant_id,
                user_id=user_id,
                goal_id=test.goal_id,
                answered_question_ids=new_answered_ids,
                previous_answers=normalized_previous,
                expected_next_question_id=expected_next_question_id,
                updated_at=datetime.now(timezone.utc),
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
                "answered_count": len(new_answered_ids),
                "completed_at": test.completed_at,
                "adaptive_decision": self.adaptive_engine_service.serialize_decision(adaptive_decision),
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
                attempt_count = int(getattr(existing_answer, "attempt_count", 1) or 1)
                evaluated_answer = DiagnosticTest.evaluate_answers(
                    [{"question_id": int(answer["question_id"]), "user_answer": answer["user_answer"], "attempt_count": attempt_count}],
                    {int(question.id): question},
                )[0]
                score = float(evaluated_answer["score"])
                accuracy = float(evaluated_answer["accuracy"])
                await self.diagnostic_repository.upsert_answer(
                    test_id=test_id,
                    question_id=answer["question_id"],
                    user_answer=answer["user_answer"],
                    score=score,
                    time_taken=answer["time_taken"],
                    accuracy=accuracy,
                    attempt_count=attempt_count,
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
            diagnostic_event = await self.learning_event_service.track_diagnostic_completed(
                tenant_id=tenant_id,
                user_id=user_id,
                diagnostic_test_id=test_id,
                goal_id=test.goal_id,
                idempotency_key=f"diagnostic-complete:{tenant_id}:{user_id}:{test_id}",
                commit=False,
            )
            await self.outbox_service.add_domain_event_message(
                event_name="diagnostic_completed",
                tenant_id=tenant_id,
                user_id=user_id,
                payload={
                    "event_id": int(diagnostic_event.id),
                    "diagnostic_test_id": int(test_id),
                    "goal_id": int(test.goal_id),
                },
                idempotency_key=f"domain-diagnostic-complete:{tenant_id}:{user_id}:{test_id}",
            )
            await self.gamification_service.award_test_completion(
                tenant_id=tenant_id,
                user_id=user_id,
                diagnostic_test_id=int(test_id),
                goal_id=int(test.goal_id),
                activity_time=datetime.now(timezone.utc),
            )
            await self.session.commit()
            await self.cache_service.bump_namespace_version(f"ai-context:user:{tenant_id}:{user_id}")
            await self.ml_platform_service.build_feature_snapshot(user_id=user_id, tenant_id=tenant_id)
            stored_answers = await self.diagnostic_repository.list_answers_for_test(test_id=test_id)
            adaptive_summary = self._build_adaptive_summary(
                answers=stored_answers,
                questions_by_id=questions_by_id,
            )
            return {
                "id": test.id,
                "user_id": test.user_id,
                "goal_id": test.goal_id,
                "started_at": test.started_at,
                "completed_at": test.completed_at,
                "adaptive_summary": adaptive_summary,
            }
        except Exception:
            await self.session.rollback()
            raise

    async def finalize_test(self, *, test_id: int, user_id: int, tenant_id: int):
        test, answers = await self.get_or_resume_test(test_id=test_id, user_id=user_id, tenant_id=tenant_id)
        if test.completed_at is not None:
            return {
                "id": test.id,
                "user_id": test.user_id,
                "goal_id": test.goal_id,
                "started_at": test.started_at,
                "completed_at": test.completed_at,
                "adaptive_summary": self._build_adaptive_summary(
                    answers=answers,
                    questions_by_id=await self._questions_by_id(tenant_id=tenant_id, question_ids=[int(answer.question_id) for answer in answers]),
                ),
            }
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

    async def _questions_by_id(self, *, tenant_id: int, question_ids: list[int]) -> dict[int, object]:
        question_rows = await self.topic_repository.list_questions_by_ids(
            tenant_id=tenant_id,
            question_ids=question_ids,
        )
        return {int(question.id): question for question in question_rows}

    def _build_adaptive_summary(self, *, answers: list[object], questions_by_id: dict[int, object]) -> dict:
        adaptive_rows = DiagnosticTest.build_adaptive_rows(
            answers=answers,
            questions_by_id=questions_by_id,
        )
        profiles = self.adaptive_engine_service.classify_topic_levels(adaptive_rows)
        return {"topic_levels": self.adaptive_engine_service.serialize_topic_profiles(profiles)}

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
        prerequisite_map: dict[int, list[int]] = {}
        prerequisite_edges = await self.topic_repository.get_prerequisite_edges(tenant_id=tenant_id)
        for topic_id, prerequisite_topic_id in prerequisite_edges:
            prerequisite_map.setdefault(int(topic_id), []).append(int(prerequisite_topic_id))
        weakness_analysis = self.weakness_engine.analyze(
            topic_scores={int(topic_id): float(score) for topic_id, score in scores.items()},
            prerequisite_map=prerequisite_map,
        )
        foundation_gap_topic_ids = sorted(
            {
                int(prerequisite_topic_id)
                for item in weakness_analysis.get("deep_weaknesses", [])
                for prerequisite_topic_id in item.get("missing_foundations", [])
            }
        )
        recommendation_levels = {
            int(topic_id): self.recommendation_service.engine.classify_topic(float(score))
            for topic_id, score in scores.items()
        }
        return {
            "test_id": test_id,
            "topic_scores": scores,
            "weak_topic_ids": [int(item["topic_id"]) for item in weakness_analysis.get("deep_weaknesses", [])],
            "foundation_gap_topic_ids": foundation_gap_topic_ids,
            "recommendation_levels": recommendation_levels,
            "roadmap": roadmap,
        }

    async def select_next_question(
        self,
        goal_id: int,
        previous_answers: list[dict],
        topic_scores: dict[int, float] | None = None,
        question_ids: list[int] | None = None,
        tenant_id: int | None = None,
    ) -> dict | None:
        if question_ids:
            questions = await self.topic_repository.list_questions_by_ids(
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

        question_lookup = {question.id: question for question in questions}
        scored_previous_answers = DiagnosticTest.evaluate_answers(previous_answers, question_lookup)
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
