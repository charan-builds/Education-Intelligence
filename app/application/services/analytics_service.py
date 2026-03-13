from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.diagnostic_test import DiagnosticTest
from app.domain.models.question import Question
from app.domain.models.roadmap import Roadmap
from app.domain.models.roadmap_step import RoadmapStep
from app.domain.models.user import User
from app.domain.models.user_answer import UserAnswer


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def topic_mastery_distribution(self, tenant_id: int) -> dict[str, int]:
        # Average score per topic (tenant scoped), then bucket by mastery bands.
        topic_avg_subquery = (
            select(Question.topic_id.label("topic_id"), func.avg(UserAnswer.score).label("avg_score"))
            .join(UserAnswer, UserAnswer.question_id == Question.id)
            .join(DiagnosticTest, DiagnosticTest.id == UserAnswer.test_id)
            .join(User, User.id == DiagnosticTest.user_id)
            .where(User.tenant_id == tenant_id)
            .group_by(Question.topic_id)
            .subquery()
        )

        result = await self.session.execute(
            select(
                func.coalesce(
                    func.sum(case((topic_avg_subquery.c.avg_score < 50, 1), else_=0)),
                    0,
                ).label("beginner"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                (topic_avg_subquery.c.avg_score >= 50)
                                & (topic_avg_subquery.c.avg_score <= 70),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("needs_practice"),
                func.coalesce(
                    func.sum(case((topic_avg_subquery.c.avg_score > 70, 1), else_=0)),
                    0,
                ).label("mastered"),
            )
        )
        beginner, needs_practice, mastered = result.one()
        return {
            "beginner": int(beginner or 0),
            "needs_practice": int(needs_practice or 0),
            "mastered": int(mastered or 0),
        }

    async def diagnostic_completion_rate(self, tenant_id: int) -> float:
        total_result = await self.session.execute(
            select(func.count(DiagnosticTest.id))
            .join(User, User.id == DiagnosticTest.user_id)
            .where(User.tenant_id == tenant_id)
        )
        completed_result = await self.session.execute(
            select(func.count(DiagnosticTest.id))
            .join(User, User.id == DiagnosticTest.user_id)
            .where(User.tenant_id == tenant_id, DiagnosticTest.completed_at.is_not(None))
        )

        total = int(total_result.scalar_one() or 0)
        completed = int(completed_result.scalar_one() or 0)
        if total == 0:
            return 0.0
        return round((completed / total) * 100, 2)

    async def roadmap_completion_rate(self, tenant_id: int) -> float:
        total_result = await self.session.execute(
            select(func.count(RoadmapStep.id))
            .join(Roadmap, Roadmap.id == RoadmapStep.roadmap_id)
            .join(User, User.id == Roadmap.user_id)
            .where(User.tenant_id == tenant_id)
        )
        completed_result = await self.session.execute(
            select(func.count(RoadmapStep.id))
            .join(Roadmap, Roadmap.id == RoadmapStep.roadmap_id)
            .join(User, User.id == Roadmap.user_id)
            .where(User.tenant_id == tenant_id, RoadmapStep.progress_status == "completed")
        )

        total = int(total_result.scalar_one() or 0)
        completed = int(completed_result.scalar_one() or 0)
        if total == 0:
            return 0.0
        return round((completed / total) * 100, 2)

    async def aggregated_metrics(self, tenant_id: int) -> dict:
        topic_distribution = await self.topic_mastery_distribution(tenant_id)
        diagnostic_rate = await self.diagnostic_completion_rate(tenant_id)
        roadmap_rate = await self.roadmap_completion_rate(tenant_id)

        return {
            "tenant_id": tenant_id,
            "topic_mastery_distribution": topic_distribution,
            "diagnostic_completion_rate": diagnostic_rate,
            "roadmap_completion_rate": roadmap_rate,
        }
