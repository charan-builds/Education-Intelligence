from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.diagnostic_test import DiagnosticTest
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

    async def list_answers_for_test(self, *, test_id: int) -> list[UserAnswer]:
        result = await self.session.execute(
            select(UserAnswer).where(UserAnswer.test_id == test_id).order_by(UserAnswer.id.asc())
        )
        return list(result.scalars().all())

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
    ) -> UserAnswer:
        answer = UserAnswer(
            test_id=test_id,
            question_id=question_id,
            user_answer=user_answer,
            score=score,
            time_taken=time_taken,
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
    ) -> UserAnswer:
        existing = await self.get_answer_for_test_question(test_id=test_id, question_id=question_id)
        if existing is not None:
            existing.user_answer = user_answer
            existing.score = score
            existing.time_taken = time_taken
            await self.session.flush()
            return existing
        return await self.add_answer(
            test_id=test_id,
            question_id=question_id,
            user_answer=user_answer,
            score=score,
            time_taken=time_taken,
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
