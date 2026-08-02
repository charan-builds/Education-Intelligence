from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.analytics_service import AnalyticsService
from app.application.services.learning_intelligence_service import LearningIntelligenceService
from app.application.services.mentor_service import MentorService
from app.application.services.precomputed_analytics_service import PrecomputedAnalyticsService
from app.domain.models.diagnostic_test import DiagnosticTest
from app.domain.models.roadmap import Roadmap
from app.domain.models.roadmap_step import RoadmapStep
from app.domain.models.topic import Topic
from app.domain.models.topic_score import TopicScore
from app.domain.models.user import User, UserRole
from app.infrastructure.repositories.roadmap_repository import RoadmapRepository
from app.infrastructure.repositories.user_goal_repository import UserGoalRepository
from app.infrastructure.repositories.tenant_scoping import tenant_user_scope, user_belongs_to_tenant, user_has_tenant_role


class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.analytics_service = AnalyticsService(session)
        self.learning_intelligence_service = LearningIntelligenceService(session)
        self.precomputed_analytics_service = PrecomputedAnalyticsService(session)
        self.roadmap_repository = RoadmapRepository(session)
        self.user_goal_repository = UserGoalRepository(session)
        self.mentor_service = MentorService(session=session)

    async def student_dashboard(self, *, user_id: int, tenant_id: int) -> dict:
        return await self.learning_intelligence_service.student_dashboard(user_id=user_id, tenant_id=tenant_id)

    async def independent_learner_dashboard(self, *, user_id: int, tenant_id: int) -> dict:
        user_result = await self.session.execute(
            select(User).where(User.id == user_id, User.tenant_id == tenant_id).limit(1)
        )
        user = user_result.scalar_one()

        active_goal = await self.user_goal_repository.get_active_for_user(user_id=user_id, tenant_id=tenant_id)

        latest_roadmap_result = await self.session.execute(
            select(Roadmap.id)
            .join(Roadmap.user)
            .where(Roadmap.user_id == user_id, tenant_user_scope(Roadmap.user, tenant_id))
            .order_by(Roadmap.id.desc())
            .limit(1)
        )
        roadmap_id = latest_roadmap_result.scalar_one_or_none()

        completion_percent = 0.0
        completed_topics = 0
        remaining_topics = 0
        roadmap_preview: list[dict] = []
        next_topic: dict | None = None

        if roadmap_id is not None:
            progress_result = await self.session.execute(
                select(
                    func.count(RoadmapStep.id),
                    func.sum(case((RoadmapStep.progress_status == "completed", 1), else_=0)),
                ).where(RoadmapStep.roadmap_id == roadmap_id)
            )
            total_steps, completed_steps = progress_result.one()
            total_steps = int(total_steps or 0)
            completed_topics = int(completed_steps or 0)
            remaining_topics = max(total_steps - completed_topics, 0)
            completion_percent = round((completed_topics / total_steps) * 100, 1) if total_steps else 0.0

            preview_result = await self.session.execute(
                select(
                    RoadmapStep.id,
                    RoadmapStep.topic_id,
                    RoadmapStep.estimated_time_hours,
                    RoadmapStep.difficulty,
                    RoadmapStep.progress_status,
                    RoadmapStep.rationale,
                    Topic.name,
                )
                .join(Topic, Topic.id == RoadmapStep.topic_id)
                .where(
                    RoadmapStep.roadmap_id == roadmap_id,
                    RoadmapStep.progress_status.in_(("pending", "in_progress")),
                )
                .order_by(
                    case((RoadmapStep.progress_status == "in_progress", 0), else_=1),
                    RoadmapStep.priority.asc(),
                    RoadmapStep.id.asc(),
                )
                .limit(5)
            )
            preview_rows = preview_result.all()
            roadmap_preview = [
                {
                    "step_id": int(row.id),
                    "topic_id": int(row.topic_id),
                    "topic_name": row.name,
                    "difficulty": row.difficulty,
                    "estimated_time_hours": float(row.estimated_time_hours),
                    "status": row.progress_status,
                }
                for row in preview_rows
            ]
            first_step = preview_rows[0] if preview_rows else None
            if first_step is not None:
                next_topic = {
                    "topic_id": int(first_step.topic_id),
                    "topic_name": first_step.name,
                    "reason": first_step.rationale or "This is the highest-priority next step in your roadmap.",
                    "estimated_time_hours": float(first_step.estimated_time_hours),
                }

        weak_topics_result = await self.session.execute(
            select(Topic.name)
            .join(TopicScore, Topic.id == TopicScore.topic_id)
            .where(
                TopicScore.user_id == user_id,
                TopicScore.tenant_id == tenant_id,
                TopicScore.score < 72.0,
            )
            .order_by(TopicScore.score.asc(), Topic.name.asc())
            .limit(5)
        )
        weak_topics = [row[0] for row in weak_topics_result.all()]

        display_name = user.full_name or user.display_name or user.email.split("@", 1)[0]

        return {
            "user_name": display_name,
            "goal": active_goal.goal.name if active_goal and active_goal.goal else None,
            "completion_percent": completion_percent,
            "completed_topics": completed_topics,
            "remaining_topics": remaining_topics,
            "next_topic": next_topic,
            "weak_topics": weak_topics,
            "roadmap_preview": roadmap_preview,
        }

    async def teacher_dashboard(self, *, tenant_id: int) -> dict:
        return await self.learning_intelligence_service.teacher_analytics(tenant_id=tenant_id)

    async def experiment_dashboard(self, *, tenant_id: int) -> dict:
        return await self.learning_intelligence_service.experiment_summary(tenant_id=tenant_id)

    async def community_dashboard(self, *, tenant_id: int) -> dict:
        return await self.learning_intelligence_service.community_summary(tenant_id=tenant_id)

    async def admin_dashboard(self, *, tenant_id: int) -> dict:
        snapshot = await self.precomputed_analytics_service.latest_tenant_dashboard(tenant_id=tenant_id)

        total_users_result = await self.session.execute(
            select(func.count(func.distinct(User.id))).where(user_belongs_to_tenant(User, tenant_id))
        )
        total_users = int(total_users_result.scalar_one() or 0)

        if snapshot is not None:
            active_learners = int(snapshot.get("active_learners") or 0)
        else:
            active_learners_result = await self.session.execute(
                select(func.count(func.distinct(User.id))).where(
                    user_has_tenant_role(User, tenant_id, UserRole.student.value)
                )
            )
            active_learners = int(active_learners_result.scalar_one() or 0)

        diagnostics_taken_result = await self.session.execute(
            select(func.count(DiagnosticTest.id))
            .join(DiagnosticTest.user)
            .where(tenant_user_scope(DiagnosticTest.user, tenant_id))
        )
        diagnostics_taken = int(diagnostics_taken_result.scalar_one() or 0)

        roadmap_completions = await self.analytics_service.roadmap_completion_rate(tenant_id)
        progress_summary = await self.analytics_service.roadmap_progress_summary(tenant_id)

        return {
            "tenant_id": tenant_id,
            "total_users": total_users,
            "active_learners": active_learners,
            "roadmap_completions": roadmap_completions,
            "diagnostics_taken": diagnostics_taken,
            "learners": progress_summary["learners"],
        }
