from collections import defaultdict

from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.precomputed_analytics_service import PrecomputedAnalyticsService
from app.domain.models.diagnostic_test import DiagnosticTest
from app.domain.models.question import Question
from app.domain.models.roadmap import Roadmap
from app.domain.models.roadmap_step import RoadmapStep
from app.domain.models.tenant import Tenant
from app.domain.models.topic import Topic
from app.domain.models.user import User, UserRole
from app.domain.models.user_tenant_role import UserTenantRole
from app.domain.models.user_answer import UserAnswer
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.repositories.topic_repository import TopicRepository
from app.infrastructure.repositories.tenant_scoping import user_belongs_to_tenant
from app.infrastructure.repositories.user_repository import UserRepository


class AnalyticsService:
    STUDENT_TOPIC_HEATMAP_SQL = """
WITH topic_rollup AS (
    SELECT
        q.topic_id,
        t.name AS topic_name,
        ROUND(AVG(ua.score)::numeric, 2) AS mastery_score,
        ROUND(AVG(ua.accuracy * 100)::numeric, 2) AS average_accuracy,
        ROUND(AVG(ua.time_taken)::numeric, 2) AS average_time_taken_seconds,
        ROUND(AVG(ua.attempt_count)::numeric, 2) AS average_attempts,
        MAX(COALESCE(le.event_timestamp, le.created_at, dt.completed_at, dt.started_at)) AS last_activity_at
    FROM user_answers ua
    JOIN diagnostic_tests dt ON dt.id = ua.test_id
    JOIN questions q ON q.id = ua.question_id
    JOIN topics t ON t.id = q.topic_id
    LEFT JOIN learning_events le
      ON le.tenant_id = :tenant_id
     AND le.user_id = dt.user_id
     AND le.topic_id = q.topic_id
    WHERE dt.user_id = :user_id
      AND dt.completed_at IS NOT NULL
      AND t.tenant_id = :tenant_id
    GROUP BY q.topic_id, t.name
)
SELECT *
FROM topic_rollup
ORDER BY mastery_score ASC, topic_name ASC
"""

    STUDENT_PERFORMANCE_TREND_SQL = """
SELECT
    to_char(date_trunc('day', dt.completed_at), 'YYYY-MM-DD') AS label,
    ROUND(AVG(ua.score)::numeric, 2) AS average_score,
    ROUND(AVG(ua.accuracy * 100)::numeric, 2) AS average_accuracy,
    ROUND(AVG(ua.time_taken)::numeric, 2) AS average_time_taken_seconds,
    COUNT(ua.id) AS answered_questions
FROM user_answers ua
JOIN diagnostic_tests dt ON dt.id = ua.test_id
JOIN questions q ON q.id = ua.question_id
JOIN topics t ON t.id = q.topic_id
WHERE dt.user_id = :user_id
  AND dt.completed_at IS NOT NULL
  AND t.tenant_id = :tenant_id
GROUP BY date_trunc('day', dt.completed_at)
ORDER BY date_trunc('day', dt.completed_at) ASC
"""

    TOPIC_LEARNER_SUMMARY_SQL = """
WITH learner_rollup AS (
    SELECT
        dt.user_id,
        ROUND(AVG(ua.score)::numeric, 2) AS mastery_score,
        ROUND(AVG(ua.accuracy * 100)::numeric, 2) AS average_accuracy,
        ROUND(AVG(ua.time_taken)::numeric, 2) AS average_time_taken_seconds,
        ROUND(AVG(ua.attempt_count)::numeric, 2) AS average_attempts
    FROM user_answers ua
    JOIN diagnostic_tests dt ON dt.id = ua.test_id
    JOIN questions q ON q.id = ua.question_id
    JOIN topics t ON t.id = q.topic_id
    WHERE q.topic_id = :topic_id
      AND dt.completed_at IS NOT NULL
      AND t.tenant_id = :tenant_id
    GROUP BY dt.user_id
)
SELECT *
FROM learner_rollup
ORDER BY mastery_score ASC, user_id ASC
"""

    TOPIC_PERFORMANCE_TREND_SQL = """
SELECT
    to_char(date_trunc('day', dt.completed_at), 'YYYY-MM-DD') AS label,
    COUNT(DISTINCT dt.user_id) AS learner_count,
    ROUND(AVG(ua.score)::numeric, 2) AS average_score,
    ROUND(AVG(ua.accuracy * 100)::numeric, 2) AS average_accuracy,
    ROUND(AVG(ua.time_taken)::numeric, 2) AS average_time_taken_seconds
FROM user_answers ua
JOIN diagnostic_tests dt ON dt.id = ua.test_id
JOIN questions q ON q.id = ua.question_id
JOIN topics t ON t.id = q.topic_id
WHERE q.topic_id = :topic_id
  AND dt.completed_at IS NOT NULL
  AND t.tenant_id = :tenant_id
GROUP BY date_trunc('day', dt.completed_at)
ORDER BY date_trunc('day', dt.completed_at) ASC
"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.cache_service = CacheService()
        self.topic_repository = TopicRepository(session)
        self.user_repository = UserRepository(session)

    async def _require_tenant_user(self, *, tenant_id: int, user_id: int) -> None:
        user = await self.user_repository.get_by_id_in_tenant(user_id, tenant_id)
        if user is None:
            raise ValueError("User not found")

    async def _require_tenant_topic(self, *, tenant_id: int, topic_id: int) -> None:
        topic = await self.topic_repository.get_topic(topic_id, tenant_id=tenant_id)
        if topic is None:
            raise ValueError("Topic not found")

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
            precomputed = await PrecomputedAnalyticsService(self.session).tenant_dashboard_from_materialized_view(tenant_id=tenant_id)
            if precomputed is not None:
                return {
                    "tenant_id": tenant_id,
                    "topic_mastery_distribution": dict(precomputed["topic_mastery_distribution"]),
                    "diagnostic_completion_rate": float(precomputed["diagnostic_completion_rate"]),
                    "roadmap_completion_rate": float(precomputed["roadmap_completion_rate"]),
                }
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
            precomputed = await PrecomputedAnalyticsService(self.session).tenant_dashboard_from_materialized_view(tenant_id=tenant_id)
            if precomputed is not None:
                return {
                    "tenant_id": tenant_id,
                    "topic_mastery_distribution": dict(precomputed["topic_mastery_distribution"]),
                }
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
            precomputed = await PrecomputedAnalyticsService(self.session).roadmap_progress_from_materialized_view(
                tenant_id=tenant_id,
                limit=limit,
                offset=offset,
            )
            if precomputed is not None:
                return precomputed
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
        dialect = str(self.session.bind.dialect.name if self.session.bind is not None else "")
        if dialect == "postgresql":
            tenant_rows = (
                await self.session.execute(
                    text(
                        """
                        SELECT
                            t.id AS tenant_id,
                            t.name AS tenant_name,
                            t.type AS tenant_type,
                            COALESCE(SUM(CASE WHEN utr.role = 'student' THEN 1 ELSE 0 END), 0) AS student_count,
                            COALESCE(SUM(CASE WHEN utr.role = 'mentor' THEN 1 ELSE 0 END), 0) AS mentor_count,
                            COALESCE(SUM(CASE WHEN utr.role = 'teacher' THEN 1 ELSE 0 END), 0) AS teacher_count,
                            COALESCE(SUM(CASE WHEN utr.role = 'admin' THEN 1 ELSE 0 END), 0) AS admin_count,
                            COALESCE(SUM(CASE WHEN utr.role = 'super_admin' THEN 1 ELSE 0 END), 0) AS super_admin_count,
                            COALESCE(tam.diagnostic_completion_rate, 0) AS diagnostic_completion_rate,
                            COALESCE(tam.roadmap_completion_rate, 0) AS roadmap_completion_rate,
                            COALESCE(ups.average_completion_percent, 0) AS average_completion_percent,
                            COALESCE(ups.average_mastery_percent, 0) AS average_mastery_percent,
                            COALESCE(tam.beginner_topics, 0) AS beginner_topics,
                            COALESCE(tam.needs_practice_topics, 0) AS needs_practice_topics,
                            COALESCE(tam.mastered_topics, 0) AS mastered_topics
                        FROM tenants t
                        LEFT JOIN user_tenant_roles utr ON utr.tenant_id = t.id
                        LEFT JOIN tenant_analytics_mv tam ON tam.tenant_id = t.id
                        LEFT JOIN (
                            SELECT
                                tenant_id,
                                ROUND(AVG(completion_percent)) AS average_completion_percent,
                                ROUND(AVG(mastery_percent)) AS average_mastery_percent
                            FROM user_progress_summary_mv
                            GROUP BY tenant_id
                        ) ups ON ups.tenant_id = t.id
                        GROUP BY
                            t.id,
                            t.name,
                            t.type,
                            tam.diagnostic_completion_rate,
                            tam.roadmap_completion_rate,
                            tam.beginner_topics,
                            tam.needs_practice_topics,
                            tam.mastered_topics,
                            ups.average_completion_percent,
                            ups.average_mastery_percent
                        ORDER BY t.name ASC
                        """
                    )
                )
            ).mappings().all()
            if tenant_rows:
                tenant_breakdown = [
                    {
                        "tenant_id": int(row["tenant_id"]),
                        "tenant_name": str(row["tenant_name"]),
                        "tenant_type": str(row["tenant_type"]),
                        "student_count": int(row["student_count"] or 0),
                        "mentor_count": int(row["mentor_count"] or 0),
                        "teacher_count": int(row["teacher_count"] or 0),
                        "admin_count": int(row["admin_count"] or 0),
                        "super_admin_count": int(row["super_admin_count"] or 0),
                        "diagnostic_completion_rate": float(row["diagnostic_completion_rate"] or 0.0),
                        "roadmap_completion_rate": float(row["roadmap_completion_rate"] or 0.0),
                        "average_completion_percent": int(row["average_completion_percent"] or 0),
                        "average_mastery_percent": int(row["average_mastery_percent"] or 0),
                    }
                    for row in tenant_rows
                ]
                student_count = sum(int(item["student_count"]) for item in tenant_breakdown)
                mentor_count = sum(int(item["mentor_count"]) for item in tenant_breakdown)
                teacher_count = sum(int(item["teacher_count"]) for item in tenant_breakdown)
                admin_count = sum(int(item["admin_count"]) for item in tenant_breakdown)
                super_admin_count = sum(int(item["super_admin_count"]) for item in tenant_breakdown)
                average_completion = round(sum(int(item["average_completion_percent"]) for item in tenant_breakdown) / len(tenant_breakdown))
                average_mastery = round(sum(int(item["average_mastery_percent"]) for item in tenant_breakdown) / len(tenant_breakdown))
                diagnostic_rate = round(sum(float(item["diagnostic_completion_rate"]) for item in tenant_breakdown) / len(tenant_breakdown), 2)
                roadmap_rate = round(sum(float(item["roadmap_completion_rate"]) for item in tenant_breakdown) / len(tenant_breakdown), 2)
                topic_distribution = {
                    "beginner": sum(int(row["beginner_topics"] or 0) for row in tenant_rows),
                    "needs_practice": sum(int(row["needs_practice_topics"] or 0) for row in tenant_rows),
                    "mastered": sum(int(row["mastered_topics"] or 0) for row in tenant_rows),
                }
                tenant_breakdown.sort(
                    key=lambda item: (
                        -int(item["student_count"]),
                        -int(item["average_mastery_percent"]),
                        str(item["tenant_name"]).lower(),
                    )
                )
                return {
                    "tenant_count": len(tenant_breakdown),
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

    @staticmethod
    def _compute_learning_efficiency(*, average_accuracy: float, average_time_taken_seconds: float, average_attempts: float) -> float:
        normalized_accuracy = max(0.0, min(100.0, float(average_accuracy)))
        speed_component = max(0.0, 100.0 - (min(float(average_time_taken_seconds), 120.0) / 120.0 * 100.0))
        attempts_component = max(0.0, 100.0 - (max(float(average_attempts) - 1.0, 0.0) * 35.0))
        return round((normalized_accuracy * 0.55) + (speed_component * 0.3) + (attempts_component * 0.15), 2)

    async def _assert_student_in_tenant(self, *, tenant_id: int, user_id: int) -> None:
        result = await self.session.execute(
            select(User.id).where(User.id == user_id, user_belongs_to_tenant(User, tenant_id)).limit(1)
        )
        if result.scalar_one_or_none() is None:
            raise ValueError("Student not found in tenant scope")

    async def student_performance_analytics(self, *, tenant_id: int, user_id: int) -> dict:
        await self._assert_student_in_tenant(tenant_id=tenant_id, user_id=user_id)
        cache_key = await self.cache_service.build_versioned_key(
            "analytics:student-performance",
            tenant_id=tenant_id,
            user_id=user_id,
        )

        async def _factory() -> dict:
            heatmap_result = await self.session.execute(
                text(self.STUDENT_TOPIC_HEATMAP_SQL),
                {"tenant_id": tenant_id, "user_id": user_id},
            )
            topic_mastery_heatmap = [
                {
                    "topic_id": int(row.topic_id),
                    "topic_name": str(row.topic_name),
                    "mastery_score": float(row.mastery_score or 0.0),
                    "average_accuracy": float(row.average_accuracy or 0.0),
                    "average_time_taken_seconds": float(row.average_time_taken_seconds or 0.0),
                    "average_attempts": float(row.average_attempts or 0.0),
                    "last_activity_at": row.last_activity_at.isoformat() if row.last_activity_at is not None else None,
                }
                for row in heatmap_result
            ]

            trend_result = await self.session.execute(
                text(self.STUDENT_PERFORMANCE_TREND_SQL),
                {"tenant_id": tenant_id, "user_id": user_id},
            )
            performance_trend = [
                {
                    "label": str(row.label),
                    "average_score": float(row.average_score or 0.0),
                    "average_accuracy": float(row.average_accuracy or 0.0),
                    "average_time_taken_seconds": float(row.average_time_taken_seconds or 0.0),
                    "answered_questions": int(row.answered_questions or 0),
                }
                for row in trend_result
            ]

            weak_topics = [
                {
                    "topic_id": item["topic_id"],
                    "topic_name": item["topic_name"],
                    "mastery_score": item["mastery_score"],
                    "average_accuracy": item["average_accuracy"],
                    "average_time_taken_seconds": item["average_time_taken_seconds"],
                    "average_attempts": item["average_attempts"],
                }
                for item in topic_mastery_heatmap[:5]
            ]

            if topic_mastery_heatmap:
                average_accuracy = sum(item["average_accuracy"] for item in topic_mastery_heatmap) / len(topic_mastery_heatmap)
                average_time = sum(item["average_time_taken_seconds"] for item in topic_mastery_heatmap) / len(topic_mastery_heatmap)
                average_attempts = sum(item["average_attempts"] for item in topic_mastery_heatmap) / len(topic_mastery_heatmap)
            else:
                average_accuracy = 0.0
                average_time = 0.0
                average_attempts = 1.0

            return {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "learning_efficiency_score": self._compute_learning_efficiency(
                    average_accuracy=average_accuracy,
                    average_time_taken_seconds=average_time,
                    average_attempts=average_attempts,
                ),
                "topic_mastery_heatmap": topic_mastery_heatmap,
                "weak_topics": weak_topics,
                "performance_trend": performance_trend,
                "sql_queries": {
                    "topic_mastery_heatmap": self.STUDENT_TOPIC_HEATMAP_SQL.strip(),
                    "performance_trend": self.STUDENT_PERFORMANCE_TREND_SQL.strip(),
                },
            }

        return await self.cache_service.get_or_set(cache_key, ttl=60, factory=_factory)

    async def topic_performance_analytics(self, *, tenant_id: int, topic_id: int) -> dict:
        await self._require_tenant_topic(tenant_id=tenant_id, topic_id=topic_id)
        topic_result = await self.session.execute(
            select(Topic.id, Topic.name).where(Topic.id == topic_id, Topic.tenant_id == tenant_id).limit(1)
        )
        topic_row = topic_result.one()

        cache_key = await self.cache_service.build_versioned_key(
            "analytics:topic-performance",
            tenant_id=tenant_id,
            topic_id=topic_id,
        )

        async def _factory() -> dict:
            learner_result = await self.session.execute(
                text(self.TOPIC_LEARNER_SUMMARY_SQL),
                {"tenant_id": tenant_id, "topic_id": topic_id},
            )
            weakest_learners = [
                {
                    "user_id": int(row.user_id),
                    "mastery_score": float(row.mastery_score or 0.0),
                    "average_accuracy": float(row.average_accuracy or 0.0),
                    "average_time_taken_seconds": float(row.average_time_taken_seconds or 0.0),
                    "average_attempts": float(row.average_attempts or 0.0),
                }
                for row in learner_result
            ]

            trend_result = await self.session.execute(
                text(self.TOPIC_PERFORMANCE_TREND_SQL),
                {"tenant_id": tenant_id, "topic_id": topic_id},
            )
            performance_trend = [
                {
                    "label": str(row.label),
                    "learner_count": int(row.learner_count or 0),
                    "average_score": float(row.average_score or 0.0),
                    "average_accuracy": float(row.average_accuracy or 0.0),
                    "average_time_taken_seconds": float(row.average_time_taken_seconds or 0.0),
                }
                for row in trend_result
            ]

            learner_count = len(weakest_learners)
            average_mastery_score = round(sum(item["mastery_score"] for item in weakest_learners) / learner_count, 2) if weakest_learners else 0.0
            average_accuracy = round(sum(item["average_accuracy"] for item in weakest_learners) / learner_count, 2) if weakest_learners else 0.0
            average_time_taken_seconds = round(
                sum(item["average_time_taken_seconds"] for item in weakest_learners) / learner_count, 2
            ) if weakest_learners else 0.0
            average_attempts = round(sum(item["average_attempts"] for item in weakest_learners) / learner_count, 2) if weakest_learners else 1.0

            return {
                "tenant_id": tenant_id,
                "topic_id": int(topic_row.id),
                "topic_name": str(topic_row.name),
                "learner_count": learner_count,
                "average_mastery_score": average_mastery_score,
                "average_accuracy": average_accuracy,
                "average_time_taken_seconds": average_time_taken_seconds,
                "learning_efficiency_score": self._compute_learning_efficiency(
                    average_accuracy=average_accuracy,
                    average_time_taken_seconds=average_time_taken_seconds,
                    average_attempts=average_attempts,
                ),
                "weakest_learners": weakest_learners[:5],
                "performance_trend": performance_trend,
                "sql_queries": {
                    "learner_summary": self.TOPIC_LEARNER_SUMMARY_SQL.strip(),
                    "performance_trend": self.TOPIC_PERFORMANCE_TREND_SQL.strip(),
                },
            }

        return await self.cache_service.get_or_set(cache_key, ttl=60, factory=_factory)
