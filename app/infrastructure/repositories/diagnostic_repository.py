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

    async def get_test_for_user(self, test_id: int, user_id: int, tenant_id: int) -> DiagnosticTest | None:
        result = await self.session.execute(
            select(DiagnosticTest)
            .join(DiagnosticTest.user)
            .where(
                DiagnosticTest.id == test_id,
                DiagnosticTest.user_id == user_id,
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
        )
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
