from __future__ import annotations

import inspect
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import NotFoundError, ValidationError
from app.application.services.adaptive_engine_service import AdaptiveEngineService
from app.application.services.diagnostic.expiry_guard import enforce_diagnostic_not_expired
from app.application.services.diagnostic.scoring_service import DiagnosticScoringService
from app.application.services.diagnostic.selection_service import AdaptiveSelectionService
from app.application.services.learning_event_service import LearningEventService
from app.application.services.skill_vector_service import SkillVectorService
from app.domain.models.diagnostic_test import DiagnosticTestStatus
from app.infrastructure.repositories.diagnostic_repository import DiagnosticRepository
from app.infrastructure.repositories.goal_repository import GoalRepository
from app.infrastructure.repositories.topic_repository import TopicRepository
from app.schemas.question_serializer import normalize_difficulty_payload, sanitize_question


class DiagnosticTestService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        diagnostic_repository: DiagnosticRepository | None = None,
        topic_repository: TopicRepository | None = None,
        goal_repository: GoalRepository | None = None,
        selection_service: AdaptiveSelectionService | None = None,
        scoring_service: DiagnosticScoringService | None = None,
        adaptive_engine_service: AdaptiveEngineService | None = None,
        learning_event_service: LearningEventService | None = None,
        skill_vector_service: SkillVectorService | None = None,
        completion_orchestrator: object | None = None,
    ):
        self.session = session
        self.diagnostic_repository = diagnostic_repository or DiagnosticRepository(session)
        self.topic_repository = topic_repository or TopicRepository(session)
        self.goal_repository = goal_repository or GoalRepository(session)
        self.scoring_service = scoring_service or DiagnosticScoringService()
        self.selection_service = selection_service or AdaptiveSelectionService(
            session,
            diagnostic_repository=self.diagnostic_repository,
            topic_repository=self.topic_repository,
            scoring_service=self.scoring_service,
        )
        self.adaptive_engine_service = adaptive_engine_service or AdaptiveEngineService()
        self.learning_event_service = learning_event_service or LearningEventService(session)
        self.skill_vector_service = skill_vector_service or SkillVectorService(session)
        self.completion_orchestrator = completion_orchestrator

    async def _list_questions_by_ids(
        self,
        *,
        tenant_id: int,
        question_ids: list[int],
        active_only: bool,
    ) -> list[object]:
        method = self.topic_repository.list_questions_by_ids
        kwargs: dict[str, object] = {
            "tenant_id": tenant_id,
            "question_ids": question_ids,
        }
        try:
            signature = inspect.signature(method)
            if "active_only" in signature.parameters:
                kwargs["active_only"] = active_only
        except (TypeError, ValueError):
            pass
        return await method(**kwargs)

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
            test = await self.diagnostic_repository.create_test(
                user_id=user_id,
                goal_id=goal_id,
                started_at=datetime.now(timezone.utc),
            )
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

    async def start_test_with_questions(
        self,
        *,
        user_id: int,
        goal_id: int,
        tenant_id: int = 1,
        question_count: int = 20,
    ) -> dict:
        try:
            goal = await self.goal_repository.get_by_id(tenant_id=tenant_id, goal_id=goal_id)
            if goal is None:
                raise NotFoundError("Goal not found")

            existing = await self.diagnostic_repository.get_latest_open_test_for_user(
                user_id=user_id,
                goal_id=goal_id,
                tenant_id=tenant_id,
            )
            existing_state = None
            answered_question_ids: list[int] = []
            previous_answers: list[dict] = []
            if existing is not None:
                existing_state, answered_question_ids, previous_answers, planned_question_ids = await self.selection_service.get_or_build_test_state(
                    test_id=int(existing.id),
                    user_id=user_id,
                    tenant_id=tenant_id,
                )
                if planned_question_ids:
                    questions = await self._list_questions_by_ids(
                        tenant_id=tenant_id,
                        question_ids=planned_question_ids,
                        active_only=True,
                    )
                    questions_by_id = {int(question.id): question for question in questions}
                    ordered_questions = [
                        questions_by_id[question_id]
                        for question_id in planned_question_ids
                        if question_id in questions_by_id
                    ]
                    return self._serialize_start_response(existing, ordered_questions)

            topic_links = await self.goal_repository.list_topic_links(tenant_id=tenant_id, goal_id=goal_id)
            topic_ids = [int(link.topic_id) for link in topic_links]
            if not topic_ids:
                raise ValidationError("Goal has no topics configured for diagnostic generation")

            test = existing
            if test is None:
                test = await self.diagnostic_repository.create_test(
                    user_id=user_id,
                    goal_id=goal_id,
                    started_at=datetime.now(timezone.utc),
                )
            questions = await self.diagnostic_repository.generate_diagnostic_test_questions(
                goal_id=goal_id,
                topics=topic_ids,
                total_questions=question_count,
            )
            if not questions:
                raise ValidationError("No diagnostic questions available for this goal")

            planned_question_ids = [int(question.id) for question in questions]
            next_question_id = next(
                (
                    int(question_id)
                    for question_id in planned_question_ids
                    if int(question_id) not in set(answered_question_ids)
                ),
                None,
            )
            await self.diagnostic_repository.upsert_test_state(
                test_id=int(test.id),
                tenant_id=tenant_id,
                user_id=user_id,
                goal_id=goal_id,
                answered_question_ids=answered_question_ids if existing_state is not None else [],
                previous_answers=previous_answers if existing_state is not None else [],
                planned_question_ids=planned_question_ids,
                expected_next_question_id=next_question_id,
                updated_at=datetime.now(timezone.utc),
            )
            await self.session.commit()

            return self._serialize_start_response(test, questions)
        except Exception:
            await self.session.rollback()
            raise

    async def get_or_resume_test(self, *, test_id: int, user_id: int, tenant_id: int):
        test = await self.diagnostic_repository.get_test_for_user(test_id, user_id, tenant_id)
        if test is None:
            raise NotFoundError("Test not found")
        answers = await self.diagnostic_repository.list_answers_for_test(test_id=test.id)
        return test, answers

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
            await enforce_diagnostic_not_expired(
                test,
                diagnostic_repository=self.diagnostic_repository,
                commit=getattr(self.session, "commit", None),
            )
            if getattr(test, "status", None) == DiagnosticTestStatus.started.value:
                mark_in_progress = getattr(self.diagnostic_repository, "mark_test_in_progress", None)
                if mark_in_progress is not None:
                    await mark_in_progress(test)
                else:
                    setattr(test, "status", DiagnosticTestStatus.in_progress.value)

            state, answered_ids, previous_answers, planned_question_ids = await self.selection_service.get_or_build_test_state(
                test_id=test.id,
                user_id=user_id,
                tenant_id=tenant_id,
                for_update=True,
            )
            if planned_question_ids and int(question_id) not in set(planned_question_ids):
                raise ValidationError("Question does not belong to this diagnostic test")

            question = await self.topic_repository.get_question(question_id, tenant_id)
            if question is None:
                question_rows = await self._list_questions_by_ids(
                    tenant_id=tenant_id,
                    question_ids=[int(question_id)],
                    active_only=False,
                )
                question = question_rows[0] if question_rows else None
            if question is None:
                raise NotFoundError(f"Question {question_id} not found")

            normalized_previous = self._replace_previous_answer(
                previous_answers=previous_answers,
                question_id=question_id,
                user_answer=user_answer,
                time_taken=time_taken,
            )
            new_answered_ids = sorted({*answered_ids, int(question_id)})
            expected_next_question_id = next(
                (
                    int(planned_question_id)
                    for planned_question_id in planned_question_ids
                    if int(planned_question_id) not in set(new_answered_ids)
                ),
                None,
            )
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
            await self.session.commit()
            return {
                "test_id": test_id,
                "question_id": question_id,
                "answered_count": len(new_answered_ids),
                "completed_at": test.completed_at,
                "adaptive_decision": {
                    "mode": "batch",
                    "status": "recorded",
                    "next_question_id": expected_next_question_id,
                    "requires_submit": True,
                },
            }
        except Exception:
            await self.session.rollback()
            raise

    async def submit_test(
        self,
        *,
        test_id: int,
        user_id: int,
        tenant_id: int,
        answers: list[dict] | None = None,
        trigger_roadmap: bool = False,
    ) -> dict:
        if self.completion_orchestrator is None:
            raise RuntimeError("DiagnosticCompletionOrchestrator is required to submit a diagnostic")
        return await self.completion_orchestrator.submit_test(
            test_id=test_id,
            user_id=user_id,
            tenant_id=tenant_id,
            answers=answers,
            trigger_roadmap=trigger_roadmap,
        )

    async def submit_answers(self, *, test_id: int, user_id: int, tenant_id: int, answers: list[dict]) -> dict:
        return await self.submit_test(
            test_id=test_id,
            user_id=user_id,
            tenant_id=tenant_id,
            answers=answers,
            trigger_roadmap=False,
        )

    @staticmethod
    def _question_difficulty(question: object) -> tuple[int, str]:
        return normalize_difficulty_payload(
            getattr(question, "difficulty", None),
            level=getattr(question, "difficulty_level", None),
            label=getattr(question, "difficulty_label", None),
        )

    @staticmethod
    def _question_type_value(question: object) -> str:
        question_type = getattr(question, "question_type", "mcq")
        return str(question_type.value if hasattr(question_type, "value") else question_type)

    @classmethod
    def _serialize_start_question(cls, question: object) -> dict:
        difficulty_level, difficulty_label = cls._question_difficulty(question)
        return sanitize_question({
            "id": int(question.id),
            "topic_id": int(question.topic_id),
            "difficulty_level": difficulty_level,
            "difficulty_label": difficulty_label,
            "question_type": cls._question_type_value(question),
            "question_text": str(question.question_text),
            "options": list(getattr(question, "options", None) or getattr(question, "answer_options", None) or []),
        })

    @classmethod
    def _serialize_start_response(cls, test: object, questions: list[object]) -> dict:
        return {
            "id": int(test.id),
            "test_id": int(test.id),
            "user_id": int(test.user_id),
            "goal_id": int(test.goal_id),
            "started_at": test.started_at,
            "test_duration": getattr(test, "test_duration", 20),
            "status": getattr(test, "status", DiagnosticTestStatus.started.value),
            "completed_at": test.completed_at,
            "expired_at": getattr(test, "expired_at", None),
            "questions": [cls._serialize_start_question(question) for question in questions],
        }

    @staticmethod
    def _replace_previous_answer(
        *,
        previous_answers: list[dict],
        question_id: int,
        user_answer: str,
        time_taken: float,
    ) -> list[dict]:
        updated_answer = {
            "question_id": int(question_id),
            "selected_answer": user_answer,
            "user_answer": user_answer,
            "time_taken": float(time_taken),
        }
        normalized_previous: list[dict] = []
        replaced = False
        for item in previous_answers:
            try:
                if int(item.get("question_id")) == int(question_id):
                    normalized_previous.append(updated_answer)
                    replaced = True
                else:
                    normalized_previous.append(item)
            except Exception:
                continue
        if not replaced:
            normalized_previous.append(updated_answer)
        return normalized_previous
