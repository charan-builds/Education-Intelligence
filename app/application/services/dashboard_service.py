from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.analytics_service import AnalyticsService
from app.application.services.learning_intelligence_service import LearningIntelligenceService
from app.application.services.mentor_service import MentorService
from app.domain.models.diagnostic_test import DiagnosticTest
from app.domain.models.user import User, UserRole
from app.infrastructure.repositories.roadmap_repository import RoadmapRepository
from app.infrastructure.repositories.tenant_scoping import tenant_user_scope, user_belongs_to_tenant, user_has_tenant_role


class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.analytics_service = AnalyticsService(session)
        self.learning_intelligence_service = LearningIntelligenceService(session)
        self.roadmap_repository = RoadmapRepository(session)
        self.mentor_service = MentorService(session=session)

    async def student_dashboard(self, *, user_id: int, tenant_id: int) -> dict:
        return await self.learning_intelligence_service.student_dashboard(user_id=user_id, tenant_id=tenant_id)

    async def teacher_dashboard(self, *, tenant_id: int) -> dict:
        return await self.learning_intelligence_service.teacher_analytics(tenant_id=tenant_id)

    async def experiment_dashboard(self, *, tenant_id: int) -> dict:
        return await self.learning_intelligence_service.experiment_summary(tenant_id=tenant_id)

    async def community_dashboard(self, *, tenant_id: int) -> dict:
        return await self.learning_intelligence_service.community_summary(tenant_id=tenant_id)

    async def admin_dashboard(self, *, tenant_id: int) -> dict:
        total_users_result = await self.session.execute(
            select(func.count(func.distinct(User.id))).where(user_belongs_to_tenant(User, tenant_id))
        )
        total_users = int(total_users_result.scalar_one() or 0)

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
