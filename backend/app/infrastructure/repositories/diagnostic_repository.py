from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import lazyload

from app.domain.models.diagnostic_test import DiagnosticTest
from app.domain.models.diagnostic_test_state import DiagnosticTestState
from app.domain.models.question import Question
from app.domain.models.user_answer import UserAnswer
from app.infrastructure.repositories.tenant_scoping import tenant_user_scope


class DiagnosticRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_test(self, user_id: int, goal_id: int, started_at: datetime) -> DiagnosticTest:
        test = DiagnosticTest(user_id=user_id, goal_id=goal_id, started_at=started_at, completed_at=None)
        self.session.add(test)
        await self.session.flush()
        return test

    async def get_test_for_user(
        self,
        test_id: int,
        user_id: int,
        tenant_id: int,
        *,
        for_update: bool = False,
    ) -> DiagnosticTest | None:
        stmt = (
            select(DiagnosticTest)
            .join(DiagnosticTest.user)
            .where(
                DiagnosticTest.id == test_id,
                DiagnosticTest.user_id == user_id,
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_open_test_for_user(self, *, user_id: int, goal_id: int, tenant_id: int) -> DiagnosticTest | None:
        result = await self.session.execute(
            select(DiagnosticTest)
            .join(DiagnosticTest.user)
            .where(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.goal_id == goal_id,
                DiagnosticTest.completed_at.is_(None),
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
            .order_by(DiagnosticTest.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def latest_goal_id_for_user(self, *, user_id: int, tenant_id: int) -> int | None:
        result = await self.session.execute(
            select(DiagnosticTest.goal_id)
            .join(DiagnosticTest.user)
            .where(
                DiagnosticTest.user_id == user_id,
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
            .order_by(DiagnosticTest.id.desc())
            .limit(1)
        )
        value = result.scalar_one_or_none()
        return int(value) if value is not None else None

    async def list_answers_for_test(self, *, test_id: int) -> list[UserAnswer]:
        result = await self.session.execute(
            select(UserAnswer).where(UserAnswer.test_id == test_id).order_by(UserAnswer.id.asc())
        )
        return list(result.scalars().all())

    async def get_test_state(
        self,
        *,
        test_id: int,
        user_id: int,
        tenant_id: int,
        for_update: bool = False,
    ) -> DiagnosticTestState | None:
        stmt = (
            select(DiagnosticTestState)
            .options(lazyload(DiagnosticTestState.test))
            .join(DiagnosticTest, DiagnosticTest.id == DiagnosticTestState.test_id)
            .join(DiagnosticTest.user)
            .where(
                DiagnosticTestState.test_id == test_id,
                DiagnosticTest.user_id == user_id,
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
        )
        if for_update:
            stmt = stmt.with_for_update(of=DiagnosticTestState)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_test_state(
        self,
        *,
        test_id: int,
        tenant_id: int,
        user_id: int,
        goal_id: int,
        answered_question_ids: list[int],
        previous_answers: list[dict],
        planned_question_ids: list[int] | None = None,
        expected_next_question_id: int | None,
        updated_at: datetime,
    ) -> DiagnosticTestState:
        state = await self.session.get(DiagnosticTestState, test_id)
        if state is None:
            state = DiagnosticTestState(
                test_id=test_id,
                tenant_id=tenant_id,
                user_id=user_id,
                goal_id=goal_id,
                answered_question_ids=list(answered_question_ids),
                previous_answers=list(previous_answers),
                planned_question_ids=list(planned_question_ids or []),
                expected_next_question_id=expected_next_question_id,
                updated_at=updated_at,
            )
            self.session.add(state)
            await self.session.flush()
            return state

        state.tenant_id = tenant_id
        state.user_id = user_id
        state.goal_id = goal_id
        state.answered_question_ids = list(answered_question_ids)
        state.previous_answers = list(previous_answers)
        if planned_question_ids is not None:
            state.planned_question_ids = list(planned_question_ids)
        state.expected_next_question_id = expected_next_question_id
        state.updated_at = updated_at
        await self.session.flush()
        return state

    async def get_answer_for_test_question(
        self,
        *,
        test_id: int,
        question_id: int,
        for_update: bool = False,
    ) -> UserAnswer | None:
        stmt = select(UserAnswer).where(UserAnswer.test_id == test_id, UserAnswer.question_id == question_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_answer(
        self,
        test_id: int,
        question_id: int,
        user_answer: str,
        score: float,
        time_taken: float,
        accuracy: float,
        attempt_count: int = 1,
    ) -> UserAnswer:
        answer = UserAnswer(
            test_id=test_id,
            question_id=question_id,
            user_answer=user_answer,
            score=score,
            time_taken=time_taken,
            accuracy=accuracy,
            attempt_count=attempt_count,
        )
        self.session.add(answer)
        await self.session.flush()
        return answer

    async def upsert_answer(
        self,
        *,
        test_id: int,
        question_id: int,
        user_answer: str,
        score: float,
        time_taken: float,
        accuracy: float,
        attempt_count: int,
    ) -> UserAnswer:
        existing = await self.get_answer_for_test_question(test_id=test_id, question_id=question_id)
        if existing is not None:
            existing.user_answer = user_answer
            existing.score = score
            existing.time_taken = time_taken
            existing.accuracy = accuracy
            existing.attempt_count = attempt_count
            await self.session.flush()
            return existing
        return await self.add_answer(
            test_id=test_id,
            question_id=question_id,
            user_answer=user_answer,
            score=score,
            time_taken=time_taken,
            accuracy=accuracy,
            attempt_count=attempt_count,
        )

    async def complete_test(self, test: DiagnosticTest, completed_at: datetime) -> DiagnosticTest:
        test.completed_at = completed_at
        await self.session.flush()
        return test

    async def topic_scores_for_test(self, test_id: int, user_id: int, tenant_id: int) -> dict[int, float]:
        result = await self.session.execute(
            select(Question.topic_id, func.avg(UserAnswer.score))
            .join(UserAnswer, UserAnswer.question_id == Question.id)
            .join(DiagnosticTest, DiagnosticTest.id == UserAnswer.test_id)
            .where(
                UserAnswer.test_id == test_id,
                DiagnosticTest.user_id == user_id,
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
            .group_by(Question.topic_id)
        )
        return {topic_id: float(avg_score) for topic_id, avg_score in result.all()}

    async def answer_analytics_for_test(
        self,
        test_id: int,
        user_id: int,
        tenant_id: int,
    ) -> dict:
        result = await self.session.execute(
            select(UserAnswer.time_taken, UserAnswer.score, Question.difficulty)
            .join(Question, Question.id == UserAnswer.question_id)
            .join(DiagnosticTest, DiagnosticTest.id == UserAnswer.test_id)
            .where(
                UserAnswer.test_id == test_id,
                DiagnosticTest.user_id == user_id,
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
            .order_by(UserAnswer.id.asc())
        )
        rows = list(result.all())
        distribution = {"easy": 0, "medium": 0, "hard": 0}
        for _, _, difficulty in rows:
            if int(difficulty) <= 1:
                distribution["easy"] += 1
            elif int(difficulty) == 2:
                distribution["medium"] += 1
            else:
                distribution["hard"] += 1

        return {
            "response_times": [float(time_taken) for time_taken, _, _ in rows],
            "accuracies": [float(score) for _, score, _ in rows],
            "difficulty_distribution": distribution,
        }

    async def answered_question_ids_for_user(self, *, user_id: int, tenant_id: int) -> list[int]:
        result = await self.session.execute(
            select(UserAnswer.question_id)
            .join(DiagnosticTest, DiagnosticTest.id == UserAnswer.test_id)
            .join(DiagnosticTest.user)
            .where(
                DiagnosticTest.user_id == user_id,
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
            .distinct()
            .order_by(UserAnswer.question_id.asc())
        )
        return [int(question_id) for question_id in result.scalars().all()]
