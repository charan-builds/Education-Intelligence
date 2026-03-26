from collections import defaultdict

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.diagnostic_test import DiagnosticTest
from app.domain.models.question import Question
from app.domain.models.roadmap import Roadmap
from app.domain.models.roadmap_step import RoadmapStep
from app.domain.models.tenant import Tenant
from app.domain.models.user import User, UserRole
from app.domain.models.user_tenant_role import UserTenantRole
from app.domain.models.user_answer import UserAnswer
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.repositories.tenant_scoping import user_belongs_to_tenant


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.cache_service = CacheService()

    @staticmethod
    def _current_completed_test_ids_subquery(tenant_id: int | None = None):
        stmt = (
            select(
                DiagnosticTest.user_id.label("user_id"),
                func.max(DiagnosticTest.id).label("test_id"),
            )
            .join(User, User.id == DiagnosticTest.user_id)
            .where(DiagnosticTest.completed_at.is_not(None))
            .group_by(DiagnosticTest.user_id)
        )
        if tenant_id is not None:
            stmt = stmt.where(user_belongs_to_tenant(User, tenant_id))
        return stmt.subquery()

    @staticmethod
    def _current_active_roadmap_ids_subquery(tenant_id: int | None = None):
        stmt = (
            select(
                Roadmap.user_id.label("user_id"),
                func.max(Roadmap.id).label("roadmap_id"),
            )
            .join(User, User.id == Roadmap.user_id)
            .where(Roadmap.status.in_(["ready", "generating"]))
            .group_by(Roadmap.user_id)
        )
        if tenant_id is not None:
            stmt = stmt.where(user_belongs_to_tenant(User, tenant_id))
        return stmt.subquery()

    async def _topic_mastery_distribution(self, tenant_id: int | None = None) -> dict[str, int]:
        current_tests = self._current_completed_test_ids_subquery(tenant_id)
        topic_avg_subquery = (
            select(Question.topic_id.label("topic_id"), func.avg(UserAnswer.score).label("avg_score"))
            .join(UserAnswer, UserAnswer.question_id == Question.id)
            .join(DiagnosticTest, DiagnosticTest.id == UserAnswer.test_id)
            .join(User, User.id == DiagnosticTest.user_id)
            .join(current_tests, current_tests.c.test_id == DiagnosticTest.id)
            .group_by(Question.topic_id)
        )
        topic_avg_subquery = topic_avg_subquery.subquery()

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

    async def topic_mastery_distribution(self, tenant_id: int) -> dict[str, int]:
        return await self._topic_mastery_distribution(tenant_id)

    async def _diagnostic_completion_rate(self, tenant_id: int | None = None) -> float:
        total_stmt = select(func.count(func.distinct(UserTenantRole.user_id))).where(UserTenantRole.role == UserRole.student)
        completed_stmt = (
            select(func.count(func.distinct(DiagnosticTest.user_id)))
            .join(User, User.id == DiagnosticTest.user_id)
            .join(UserTenantRole, UserTenantRole.user_id == User.id)
            .where(DiagnosticTest.completed_at.is_not(None), UserTenantRole.role == UserRole.student)
        )
        if tenant_id is not None:
            total_stmt = select(func.count(func.distinct(UserTenantRole.user_id))).where(
                UserTenantRole.tenant_id == tenant_id,
                UserTenantRole.role == UserRole.student,
            )
            completed_stmt = completed_stmt.where(UserTenantRole.tenant_id == tenant_id)

        total_result = await self.session.execute(total_stmt)
        completed_result = await self.session.execute(completed_stmt)

        total = int(total_result.scalar_one() or 0)
        completed = int(completed_result.scalar_one() or 0)
        if total == 0:
            return 0.0
        return round((completed / total) * 100, 2)

    async def diagnostic_completion_rate(self, tenant_id: int) -> float:
        return await self._diagnostic_completion_rate(tenant_id)

    async def _roadmap_completion_rate(self, tenant_id: int | None = None) -> float:
        current_roadmaps = self._current_active_roadmap_ids_subquery(tenant_id)
        total_stmt = (
            select(func.count(RoadmapStep.id))
            .join(Roadmap, Roadmap.id == RoadmapStep.roadmap_id)
            .join(User, User.id == Roadmap.user_id)
            .join(current_roadmaps, current_roadmaps.c.roadmap_id == Roadmap.id)
        )
        completed_stmt = (
            select(func.count(RoadmapStep.id))
            .join(Roadmap, Roadmap.id == RoadmapStep.roadmap_id)
            .join(User, User.id == Roadmap.user_id)
            .join(current_roadmaps, current_roadmaps.c.roadmap_id == Roadmap.id)
            .where(RoadmapStep.progress_status == "completed")
        )
        if tenant_id is not None:
            total_stmt = total_stmt.where(user_belongs_to_tenant(User, tenant_id))
            completed_stmt = completed_stmt.where(user_belongs_to_tenant(User, tenant_id))

        total_result = await self.session.execute(total_stmt)
        completed_result = await self.session.execute(completed_stmt)

        total = int(total_result.scalar_one() or 0)
        completed = int(completed_result.scalar_one() or 0)
        if total == 0:
            return 0.0
        return round((completed / total) * 100, 2)

    async def roadmap_completion_rate(self, tenant_id: int) -> float:
        return await self._roadmap_completion_rate(tenant_id)

    async def aggregated_metrics(self, tenant_id: int) -> dict:
        cache_key = await self.cache_service.build_versioned_key("analytics:overview", tenant_id=tenant_id)
        async def _factory() -> dict:
            topic_distribution = await self.topic_mastery_distribution(tenant_id)
            diagnostic_rate = await self.diagnostic_completion_rate(tenant_id)
            roadmap_rate = await self.roadmap_completion_rate(tenant_id)
            return {
                "tenant_id": tenant_id,
                "topic_mastery_distribution": topic_distribution,
                "diagnostic_completion_rate": diagnostic_rate,
                "roadmap_completion_rate": roadmap_rate,
            }
        return await self.cache_service.get_or_set(cache_key, ttl=60, factory=_factory)

    async def topic_mastery_summary(self, tenant_id: int) -> dict:
        cache_key = await self.cache_service.build_versioned_key("analytics:topic-mastery", tenant_id=tenant_id)
        async def _factory() -> dict:
            return {
                "tenant_id": tenant_id,
                "topic_mastery_distribution": await self.topic_mastery_distribution(tenant_id),
            }
        return await self.cache_service.get_or_set(cache_key, ttl=120, factory=_factory)

    async def _roadmap_progress_rows(self, tenant_id: int | None = None) -> list[dict[str, int | str]]:
        current_roadmaps = self._current_active_roadmap_ids_subquery(tenant_id)
        completed_case = case((RoadmapStep.progress_status == "completed", 1), else_=0)
        in_progress_case = case((RoadmapStep.progress_status == "in_progress", 1), else_=0)
        pending_case = case((RoadmapStep.progress_status == "pending", 1), else_=0)

        stmt = (
            select(
                UserTenantRole.tenant_id.label("tenant_id"),
                Tenant.name.label("tenant_name"),
                User.id.label("user_id"),
                User.email.label("email"),
                func.count(RoadmapStep.id).label("total_steps"),
                func.coalesce(func.sum(completed_case), 0).label("completed_steps"),
                func.coalesce(func.sum(in_progress_case), 0).label("in_progress_steps"),
                func.coalesce(func.sum(pending_case), 0).label("pending_steps"),
            )
            .select_from(UserTenantRole)
            .join(User, User.id == UserTenantRole.user_id)
            .join(Tenant, Tenant.id == UserTenantRole.tenant_id)
            .outerjoin(current_roadmaps, current_roadmaps.c.user_id == User.id)
            .outerjoin(Roadmap, Roadmap.id == current_roadmaps.c.roadmap_id)
            .outerjoin(RoadmapStep, RoadmapStep.roadmap_id == Roadmap.id)
            .where(UserTenantRole.role == UserRole.student)
            .group_by(UserTenantRole.tenant_id, Tenant.name, User.id, User.email)
            .order_by(Tenant.name.asc(), User.email.asc())
        )
        if tenant_id is not None:
            stmt = stmt.where(UserTenantRole.tenant_id == tenant_id)

        result = await self.session.execute(stmt)

        learners: list[dict[str, int | str]] = []

        for row in result.all():
            total_steps = int(row.total_steps or 0)
            completed_steps = int(row.completed_steps or 0)
            in_progress_steps = int(row.in_progress_steps or 0)
            pending_steps = int(row.pending_steps or 0)
            completion_percent = round((completed_steps / total_steps) * 100) if total_steps > 0 else 0
            mastery_percent = (
                round(((completed_steps * 100) + (in_progress_steps * 60) + (pending_steps * 20)) / total_steps)
                if total_steps > 0
                else 0
            )

            learners.append(
                {
                    "tenant_id": int(row.tenant_id),
                    "tenant_name": row.tenant_name,
                    "user_id": int(row.user_id),
                    "email": row.email,
                    "total_steps": total_steps,
                    "completed_steps": completed_steps,
                    "in_progress_steps": in_progress_steps,
                    "pending_steps": pending_steps,
                    "completion_percent": completion_percent,
                    "mastery_percent": mastery_percent,
                }
            )
        return learners

    async def roadmap_progress_summary(self, tenant_id: int, *, limit: int = 20, offset: int = 0) -> dict:
        cache_key = await self.cache_service.build_versioned_key(
            "analytics:roadmap-progress",
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )
        async def _factory() -> dict:
            learners = await self._roadmap_progress_rows(tenant_id)
            total_completion = sum(int(learner["completion_percent"]) for learner in learners)
            total_mastery = sum(int(learner["mastery_percent"]) for learner in learners)

            student_count = len(learners)
            average_completion = round(total_completion / student_count) if student_count > 0 else 0
            average_mastery = round(total_mastery / student_count) if student_count > 0 else 0
            page_items = learners[offset : offset + limit]
            next_offset = offset + limit if (offset + limit) < student_count else None

            return {
                "tenant_id": tenant_id,
                "student_count": student_count,
                "average_completion_percent": average_completion,
                "average_mastery_percent": average_mastery,
                "learners": [
                    {
                        "user_id": int(learner["user_id"]),
                        "email": str(learner["email"]),
                        "total_steps": int(learner["total_steps"]),
                        "completed_steps": int(learner["completed_steps"]),
                        "in_progress_steps": int(learner["in_progress_steps"]),
                        "pending_steps": int(learner["pending_steps"]),
                        "completion_percent": int(learner["completion_percent"]),
                        "mastery_percent": int(learner["mastery_percent"]),
                    }
                    for learner in page_items
                ],
                "meta": {
                    "total": student_count,
                    "limit": limit,
                    "offset": offset,
                    "next_offset": next_offset,
                    "next_cursor": None,
                },
            }
        return await self.cache_service.get_or_set(cache_key, ttl=60, factory=_factory)

    async def _tenant_role_breakdown(self) -> list[dict[str, int | str]]:
        result = await self.session.execute(
            select(
                Tenant.id.label("tenant_id"),
                Tenant.name.label("tenant_name"),
                Tenant.type.label("tenant_type"),
                func.coalesce(func.sum(case((UserTenantRole.role == UserRole.student, 1), else_=0)), 0).label("student_count"),
                func.coalesce(func.sum(case((UserTenantRole.role == UserRole.mentor, 1), else_=0)), 0).label("mentor_count"),
                func.coalesce(func.sum(case((UserTenantRole.role == UserRole.teacher, 1), else_=0)), 0).label("teacher_count"),
                func.coalesce(func.sum(case((UserTenantRole.role == UserRole.admin, 1), else_=0)), 0).label("admin_count"),
                func.coalesce(func.sum(case((UserTenantRole.role == UserRole.super_admin, 1), else_=0)), 0).label("super_admin_count"),
            )
            .select_from(Tenant)
            .outerjoin(UserTenantRole, UserTenantRole.tenant_id == Tenant.id)
            .group_by(Tenant.id, Tenant.name, Tenant.type)
            .order_by(Tenant.name.asc())
        )
        return [
            {
                "tenant_id": int(row.tenant_id),
                "tenant_name": row.tenant_name,
                "tenant_type": getattr(row.tenant_type, "value", str(row.tenant_type)),
                "student_count": int(row.student_count or 0),
                "mentor_count": int(row.mentor_count or 0),
                "teacher_count": int(row.teacher_count or 0),
                "admin_count": int(row.admin_count or 0),
                "super_admin_count": int(row.super_admin_count or 0),
            }
            for row in result.all()
        ]

    async def _diagnostic_completion_rates_by_tenant(self) -> dict[int, float]:
        result = await self.session.execute(
            select(
                UserTenantRole.tenant_id.label("tenant_id"),
                func.count(func.distinct(UserTenantRole.user_id)).label("total"),
                func.coalesce(
                    func.count(func.distinct(case((DiagnosticTest.completed_at.is_not(None), DiagnosticTest.user_id)))),
                    0,
                ).label("completed"),
            )
            .select_from(UserTenantRole)
            .outerjoin(DiagnosticTest, DiagnosticTest.user_id == UserTenantRole.user_id)
            .where(UserTenantRole.role == UserRole.student)
            .group_by(UserTenantRole.tenant_id)
        )
        return {
            int(row.tenant_id): round((int(row.completed or 0) / int(row.total or 0)) * 100, 2)
            if int(row.total or 0) > 0
            else 0.0
            for row in result.all()
        }

    async def _roadmap_completion_rates_by_tenant(self) -> dict[int, float]:
        current_roadmaps = self._current_active_roadmap_ids_subquery()
        result = await self.session.execute(
            select(
                UserTenantRole.tenant_id.label("tenant_id"),
                func.count(RoadmapStep.id).label("total"),
                func.coalesce(
                    func.sum(case((RoadmapStep.progress_status == "completed", 1), else_=0)),
                    0,
                ).label("completed"),
            )
            .select_from(RoadmapStep)
            .join(Roadmap, Roadmap.id == RoadmapStep.roadmap_id)
            .join(User, User.id == Roadmap.user_id)
            .join(UserTenantRole, UserTenantRole.user_id == User.id)
            .join(current_roadmaps, current_roadmaps.c.roadmap_id == Roadmap.id)
            .where(UserTenantRole.role == UserRole.student)
            .group_by(UserTenantRole.tenant_id)
        )
        return {
            int(row.tenant_id): round((int(row.completed or 0) / int(row.total or 0)) * 100, 2)
            if int(row.total or 0) > 0
            else 0.0
            for row in result.all()
        }

    async def platform_overview(self) -> dict:
        tenant_roles = await self._tenant_role_breakdown()
        learner_rows = await self._roadmap_progress_rows()
        diagnostic_rates = await self._diagnostic_completion_rates_by_tenant()
        roadmap_rates = await self._roadmap_completion_rates_by_tenant()
        topic_distribution = await self._topic_mastery_distribution()
        diagnostic_rate = await self._diagnostic_completion_rate()
        roadmap_rate = await self._roadmap_completion_rate()

        tenant_progress: dict[int, dict[str, int]] = defaultdict(
            lambda: {"student_count": 0, "completion_total": 0, "mastery_total": 0}
        )
        for learner in learner_rows:
            tenant_id = int(learner["tenant_id"])
            tenant_progress[tenant_id]["student_count"] += 1
            tenant_progress[tenant_id]["completion_total"] += int(learner["completion_percent"])
            tenant_progress[tenant_id]["mastery_total"] += int(learner["mastery_percent"])

        student_count = sum(int(item["student_count"]) for item in tenant_roles)
        mentor_count = sum(int(item["mentor_count"]) for item in tenant_roles)
        teacher_count = sum(int(item["teacher_count"]) for item in tenant_roles)
        admin_count = sum(int(item["admin_count"]) for item in tenant_roles)
        super_admin_count = sum(int(item["super_admin_count"]) for item in tenant_roles)

        average_completion = (
            round(sum(int(learner["completion_percent"]) for learner in learner_rows) / len(learner_rows))
            if learner_rows
            else 0
        )
        average_mastery = (
            round(sum(int(learner["mastery_percent"]) for learner in learner_rows) / len(learner_rows))
            if learner_rows
            else 0
        )

        tenant_breakdown: list[dict[str, int | float | str]] = []
        for tenant in tenant_roles:
            tenant_id = int(tenant["tenant_id"])
            progress = tenant_progress[tenant_id]
            tenant_student_count = int(progress["student_count"])
            average_tenant_completion = (
                round(progress["completion_total"] / tenant_student_count) if tenant_student_count > 0 else 0
            )
            average_tenant_mastery = (
                round(progress["mastery_total"] / tenant_student_count) if tenant_student_count > 0 else 0
            )
            tenant_breakdown.append(
                {
                    **tenant,
                    "diagnostic_completion_rate": diagnostic_rates.get(tenant_id, 0.0),
                    "roadmap_completion_rate": roadmap_rates.get(tenant_id, 0.0),
                    "average_completion_percent": average_tenant_completion,
                    "average_mastery_percent": average_tenant_mastery,
                }
            )

        tenant_breakdown.sort(
            key=lambda item: (
                -int(item["student_count"]),
                -int(item["average_mastery_percent"]),
                str(item["tenant_name"]).lower(),
            )
        )

        return {
            "tenant_count": len(tenant_roles),
            "student_count": student_count,
            "mentor_count": mentor_count,
            "teacher_count": teacher_count,
            "admin_count": admin_count,
            "super_admin_count": super_admin_count,
            "diagnostic_completion_rate": diagnostic_rate,
            "roadmap_completion_rate": roadmap_rate,
            "average_completion_percent": average_completion,
            "average_mastery_percent": average_mastery,
            "topic_mastery_distribution": topic_distribution,
            "tenant_breakdown": tenant_breakdown,
        }
