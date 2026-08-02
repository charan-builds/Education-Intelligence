from __future__ import annotations

import inspect
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import NotFoundError, ValidationError
from app.application.services.adaptive_engine_service import AdaptiveEngineService
from app.application.services.diagnostic.expiry_guard import (
    DEFAULT_TEST_DURATION_MINUTES,
    diagnostic_expires_at,
    enforce_diagnostic_not_expired,
)
from app.application.services.diagnostic.scoring_service import DiagnosticScoringService
from app.application.services.diagnostic.selection_service import AdaptiveSelectionService
from app.application.services.gamification_service import GamificationService
from app.application.services.learning_event_service import LearningEventService
from app.application.services.ml_platform_service import MLPlatformService
from app.application.services.outbox_service import OutboxService
from app.application.services.retention_service import RetentionService
from app.application.services.roadmap_service import RoadmapService
from app.application.services.skill_vector_service import SkillVectorService
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.repositories.diagnostic_repository import DiagnosticRepository
from app.infrastructure.repositories.topic_repository import TopicRepository
from app.schemas.question_serializer import normalize_difficulty_payload


class DiagnosticCompletionOrchestrator:
    def __init__(
        self,
        session: AsyncSession,
        *,
        diagnostic_repository: DiagnosticRepository | None = None,
        topic_repository: TopicRepository | None = None,
        selection_service: AdaptiveSelectionService | None = None,
        scoring_service: DiagnosticScoringService | None = None,
        adaptive_engine_service: AdaptiveEngineService | None = None,
        learning_event_service: LearningEventService | None = None,
        outbox_service: OutboxService | None = None,
        gamification_service: GamificationService | None = None,
        retention_service: RetentionService | None = None,
        skill_vector_service: SkillVectorService | None = None,
        ml_platform_service: MLPlatformService | None = None,
        cache_service: CacheService | None = None,
        roadmap_service: RoadmapService | None = None,
    ):
        self.session = session
        self.diagnostic_repository = diagnostic_repository or DiagnosticRepository(session)
        self.topic_repository = topic_repository or TopicRepository(session)
        self.selection_service = selection_service or AdaptiveSelectionService(
            session,
            diagnostic_repository=self.diagnostic_repository,
            topic_repository=self.topic_repository,
        )
        self.scoring_service = scoring_service or DiagnosticScoringService()
        self.adaptive_engine_service = adaptive_engine_service or AdaptiveEngineService()
        self.learning_event_service = learning_event_service or LearningEventService(session)
        self.outbox_service = outbox_service or OutboxService(session)
        self.gamification_service = gamification_service or GamificationService(session)
        self.retention_service = retention_service or RetentionService(session)
        self.skill_vector_service = skill_vector_service or SkillVectorService(session)
        self.ml_platform_service = ml_platform_service or MLPlatformService(session)
        self.cache_service = cache_service or CacheService()
        self.roadmap_service = roadmap_service or RoadmapService(session)

    async def submit_test(
        self,
        *,
        test_id: int,
        user_id: int,
        tenant_id: int,
        answers: list[dict] | None = None,
        trigger_roadmap: bool = False,
    ) -> dict:
        if answers:
            result = await self.submit_answers(
                test_id=test_id,
                user_id=user_id,
                tenant_id=tenant_id,
                answers=answers,
            )
        else:
            result = await self.finalize_test(test_id=test_id, user_id=user_id, tenant_id=tenant_id)

        if trigger_roadmap:
            await self.trigger_roadmap_generation(
                user_id=user_id,
                tenant_id=tenant_id,
                goal_id=int(result["goal_id"]),
                test_id=test_id,
            )
        return result

    async def submit_answers(
        self,
        *,
        test_id: int,
        user_id: int,
        tenant_id: int,
        answers: list[dict],
    ) -> dict:
        try:
            test = await self.diagnostic_repository.get_test_for_user(test_id, user_id, tenant_id, for_update=True)
            if not test:
                raise NotFoundError("Test not found")
            if test.completed_at is not None:
                raise ValidationError("Diagnostic test already completed")
            await enforce_diagnostic_not_expired(
                test,
                diagnostic_repository=self.diagnostic_repository,
                commit=self.session.commit,
            )
            if not answers:
                raise ValidationError("At least one answer is required")

            normalized_answers, seen_question_ids = self._normalize_submitted_answers(answers)
            state, _, _, planned_question_ids = await self.selection_service.get_or_build_test_state(
                test_id=test.id,
                user_id=user_id,
                tenant_id=tenant_id,
                for_update=True,
            )
            allowed_question_ids = set(
                int(question_id) for question_id in (planned_question_ids or state.planned_question_ids or [])
            )
            if allowed_question_ids:
                submitted_ids = {int(answer["question_id"]) for answer in normalized_answers}
                invalid_ids = sorted(submitted_ids - allowed_question_ids)
                if invalid_ids:
                    raise ValidationError(f"Answers contain questions outside this diagnostic test: {invalid_ids}")
                missing_ids = sorted(allowed_question_ids - submitted_ids)
                if missing_ids:
                    raise ValidationError(f"Answers are required for all diagnostic questions: {missing_ids}")

            question_ids = [int(answer["question_id"]) for answer in normalized_answers]
            questions_by_id = await self._questions_by_id(tenant_id=tenant_id, question_ids=question_ids)
            missing_question_ids = sorted(set(question_ids) - set(questions_by_id))
            if missing_question_ids:
                raise NotFoundError(f"Questions not found: {missing_question_ids}")

            submitted_results: list[dict] = []
            previous_answers: list[dict] = []
            for answer in normalized_answers:
                question = questions_by_id[int(answer["question_id"])]
                existing_answer = await self.diagnostic_repository.get_answer_for_test_question(
                    test_id=test_id,
                    question_id=answer["question_id"],
                    for_update=True,
                )
                attempt_count = int(getattr(existing_answer, "attempt_count", 0) or 0) + 1
                scored = self.scoring_service.score_question_answer(
                    question=question,
                    question_id=int(answer["question_id"]),
                    user_answer=answer["user_answer"],
                    attempt_count=attempt_count,
                )
                score = float(scored["score"])
                accuracy = float(scored["accuracy"])
                is_correct = bool(scored["is_correct"])
                difficulty_level, difficulty_label = normalize_difficulty_payload(
                    getattr(question, "difficulty", None),
                    level=getattr(question, "difficulty_level", None),
                    label=getattr(question, "difficulty_label", None),
                )
                await self._upsert_scored_answer(
                    test_id=test_id,
                    question_id=answer["question_id"],
                    user_answer=answer["user_answer"],
                    score=score,
                    time_taken=answer["time_taken"],
                    accuracy=accuracy,
                    is_correct=is_correct,
                    attempt_count=attempt_count,
                )
                previous_answers.append(
                    {
                        "question_id": int(answer["question_id"]),
                        "user_answer": answer["user_answer"],
                        "time_taken": float(answer["time_taken"]),
                        "score": score,
                        "accuracy": accuracy,
                        "attempt_count": attempt_count,
                    }
                )
                submitted_results.append(
                    {
                        "question_id": int(answer["question_id"]),
                        "selected_answer": answer["selected_answer"],
                        "is_correct": is_correct,
                        "score": score,
                        "time_taken": float(answer["time_taken"]),
                        "difficulty_weight": int(scored["difficulty_weight"]),
                        "difficulty_level": difficulty_level,
                        "difficulty_label": difficulty_label,
                    }
                )
                if existing_answer is None:
                    await self._track_answered_question(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        test_id=test_id,
                        question=question,
                        score=score,
                        time_taken=answer["time_taken"],
                    )

            if hasattr(self.diagnostic_repository, "upsert_test_state"):
                await self.diagnostic_repository.upsert_test_state(
                    test_id=test.id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    goal_id=test.goal_id,
                    answered_question_ids=sorted(seen_question_ids),
                    previous_answers=previous_answers,
                    planned_question_ids=planned_question_ids or None,
                    expected_next_question_id=None,
                    updated_at=datetime.now(timezone.utc),
                )
            await self._complete_test_side_effects(
                test=test,
                test_id=test_id,
                user_id=user_id,
                tenant_id=tenant_id,
            )
            await self.session.commit()
            await self.cache_service.bump_namespace_version(f"ai-context:user:{tenant_id}:{user_id}")
            await self.ml_platform_service.build_feature_snapshot(user_id=user_id, tenant_id=tenant_id)

            stored_answers = await self.diagnostic_repository.list_answers_for_test(test_id=test_id)
            adaptive_summary = self.build_adaptive_summary(
                answers=stored_answers,
                questions_by_id=questions_by_id,
            )
            response_answers = [
                {key: value for key, value in result.items() if key != "is_correct"}
                for result in submitted_results
            ]
            return {
                "id": test.id,
                "test_id": test.id,
                "user_id": test.user_id,
                "goal_id": test.goal_id,
                "started_at": test.started_at,
                "test_duration": getattr(test, "test_duration", DEFAULT_TEST_DURATION_MINUTES),
                "status": getattr(test, "status", "submitted"),
                "completed_at": test.completed_at,
                "expired_at": getattr(test, "expired_at", None),
                "adaptive_summary": adaptive_summary,
                "answered_count": len(submitted_results),
                "total_score": self.scoring_service.total_score(submitted_results),
                "percentage_score": self.scoring_service.percentage_score(submitted_results),
                "answers": response_answers,
            }
        except Exception:
            await self.session.rollback()
            raise

    async def finalize_test(self, *, test_id: int, user_id: int, tenant_id: int) -> dict:
        test = await self.diagnostic_repository.get_test_for_user(test_id, user_id, tenant_id, for_update=True)
        if test is None:
            raise NotFoundError("Test not found")
        answers = await self.diagnostic_repository.list_answers_for_test(test_id=test.id)
        if test.completed_at is not None:
            questions_by_id = await self._questions_by_id(
                tenant_id=tenant_id,
                question_ids=[int(answer.question_id) for answer in answers],
            )
            return {
                "id": test.id,
                "test_id": test.id,
                "user_id": test.user_id,
                "goal_id": test.goal_id,
                "started_at": test.started_at,
                "test_duration": getattr(test, "test_duration", DEFAULT_TEST_DURATION_MINUTES),
                "status": getattr(test, "status", "submitted"),
                "completed_at": test.completed_at,
                "expired_at": getattr(test, "expired_at", None),
                "adaptive_summary": self.build_adaptive_summary(
                    answers=answers,
                    questions_by_id=questions_by_id,
                ),
            }

        await enforce_diagnostic_not_expired(
            test,
            diagnostic_repository=self.diagnostic_repository,
            commit=self.session.commit,
        )

        state, _, previous_answers, _ = await self.selection_service.get_or_build_test_state(
            test_id=test_id,
            user_id=user_id,
            tenant_id=tenant_id,
            for_update=True,
        )
        draft_answers = previous_answers or [
            {
                "question_id": answer.question_id,
                "user_answer": answer.user_answer,
                "time_taken": answer.time_taken,
            }
            for answer in answers
        ]
        if not draft_answers:
            raise ValidationError("At least one answer is required")
        return await self.submit_answers(
            test_id=test_id,
            user_id=user_id,
            tenant_id=tenant_id,
            answers=[
                {
                    "question_id": answer["question_id"],
                    "user_answer": answer.get("user_answer") or answer.get("selected_answer"),
                    "time_taken": answer["time_taken"],
                }
                for answer in draft_answers
            ],
        )

    async def trigger_roadmap_generation(
        self,
        *,
        user_id: int,
        tenant_id: int,
        goal_id: int,
        test_id: int,
    ) -> bool:
        _, should_enqueue = await self.roadmap_service.ensure_generation_requested(
            user_id=user_id,
            tenant_id=tenant_id,
            goal_id=goal_id,
            test_id=test_id,
        )
        if should_enqueue:
            await self.outbox_service.add_task_event(
                task_name="jobs.generate_roadmap",
                args=[user_id, tenant_id, goal_id, test_id],
                tenant_id=tenant_id,
                idempotency_key=f"roadmap-generate:{user_id}:{goal_id}:{test_id}",
            )
            await self.session.commit()
        return bool(should_enqueue)

    async def get_or_resume_test(self, *, test_id: int, user_id: int, tenant_id: int):
        test = await self.diagnostic_repository.get_test_for_user(test_id, user_id, tenant_id)
        if test is None:
            raise NotFoundError("Test not found")
        answers = await self.diagnostic_repository.list_answers_for_test(test_id=test.id)
        return test, answers

    async def _mark_expired_if_late(self, test: object) -> bool:
        await enforce_diagnostic_not_expired(test, diagnostic_repository=self.diagnostic_repository)
        return False

    @classmethod
    def _expires_at(cls, test: object) -> datetime:
        return diagnostic_expires_at(test)

    async def _questions_by_id(self, *, tenant_id: int, question_ids: list[int]) -> dict[int, object]:
        method = self.topic_repository.list_questions_by_ids
        kwargs: dict[str, object] = {"tenant_id": tenant_id, "question_ids": question_ids}
        try:
            signature = inspect.signature(method)
            if "active_only" in signature.parameters:
                kwargs["active_only"] = False
        except (TypeError, ValueError):
            pass
        question_rows = await method(**kwargs)
        return {int(question.id): question for question in question_rows}

    def build_adaptive_summary(self, *, answers: list[object], questions_by_id: dict[int, object]) -> dict:
        adaptive_rows = self.scoring_service.build_adaptive_rows(
            answers=answers,
            questions_by_id=questions_by_id,
        )
        profiles = self.adaptive_engine_service.classify_topic_levels(adaptive_rows)
        return {"topic_levels": self.adaptive_engine_service.serialize_topic_profiles(profiles)}

    @staticmethod
    def _normalize_submitted_answers(answers: list[dict]) -> tuple[list[dict], set[int]]:
        normalized_answers: list[dict] = []
        seen_question_ids: set[int] = set()
        for answer in answers:
            question_id = int(answer["question_id"])
            if question_id in seen_question_ids:
                raise ValidationError(f"Duplicate answer submitted for question {question_id}")
            selected_answer = str(answer.get("selected_answer") or answer.get("user_answer") or "").strip()
            if not selected_answer:
                raise ValidationError(f"selected_answer is required for question {question_id}")
            seen_question_ids.add(question_id)
            normalized_answers.append(
                {
                    "question_id": question_id,
                    "selected_answer": selected_answer,
                    "user_answer": selected_answer,
                    "time_taken": float(answer["time_taken"]),
                }
            )
        return normalized_answers, seen_question_ids

    async def _track_answered_question(
        self,
        *,
        tenant_id: int,
        user_id: int,
        test_id: int,
        question: object,
        score: float,
        time_taken: float,
    ) -> None:
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

    async def _upsert_scored_answer(
        self,
        *,
        test_id: int,
        question_id: int,
        user_answer: str,
        score: float,
        time_taken: float,
        accuracy: float,
        is_correct: bool,
        attempt_count: int,
    ) -> None:
        try:
            await self.diagnostic_repository.upsert_answer(
                test_id=test_id,
                question_id=question_id,
                user_answer=user_answer,
                score=score,
                time_taken=time_taken,
                accuracy=accuracy,
                is_correct=is_correct,
                attempt_count=attempt_count,
            )
        except TypeError as exc:
            if "is_correct" not in str(exc):
                raise
            await self.diagnostic_repository.upsert_answer(
                test_id=test_id,
                question_id=question_id,
                user_answer=user_answer,
                score=score,
                time_taken=time_taken,
                accuracy=accuracy,
                attempt_count=attempt_count,
            )

    async def _complete_test_side_effects(self, *, test: object, test_id: int, user_id: int, tenant_id: int) -> None:
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
