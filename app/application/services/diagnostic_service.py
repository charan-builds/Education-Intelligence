from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.feature_flags import FeatureFlagService
from app.domain.engines.adaptive_testing_engine import AdaptiveTestingEngine
from app.infrastructure.repositories.diagnostic_repository import DiagnosticRepository
from app.infrastructure.repositories.topic_repository import TopicRepository
from app.application.exceptions import NotFoundError


class DiagnosticService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.diagnostic_repository = DiagnosticRepository(session)
        self.topic_repository = TopicRepository(session)
        self.adaptive_engine = AdaptiveTestingEngine()
        self.feature_flag_service = FeatureFlagService(session)

    async def start_test(self, user_id: int, goal_id: int):
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
                await self.diagnostic_repository.add_answer(
                    test_id=test_id,
                    question_id=answer["question_id"],
                    user_answer=answer["user_answer"],
                    score=answer["score"],
                    time_taken=answer["time_taken"],
                )

            await self.diagnostic_repository.complete_test(test, datetime.now(timezone.utc))
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
        questions = await self.topic_repository.list_questions_for_goal(goal_id=goal_id)
        adaptive_enabled = True
        if tenant_id is not None:
            adaptive_enabled = await self.feature_flag_service.is_enabled(
                "adaptive_testing_enabled",
                tenant_id,
            )
        next_question = self.adaptive_engine.select_next_question(
            questions=questions,
            previous_answers=previous_answers,
            topic_scores=topic_scores,
            feature_flags={"adaptive_testing_enabled": adaptive_enabled},
        )
        if next_question is None:
            return None
        return {
            "id": next_question.id,
            "topic_id": next_question.topic_id,
            "difficulty": next_question.difficulty,
            "difficulty_label": {1: "easy", 2: "medium", 3: "hard"}.get(next_question.difficulty, "medium"),
            "question_text": next_question.question_text,
        }
