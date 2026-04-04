from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.analytics_snapshot_service import AnalyticsSnapshotService
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
    DEFAULT_REBUILD_ESTIMATED_TIME_SECONDS = 30
    STALE_SNAPSHOT_THRESHOLD = timedelta(minutes=5)
    SNAPSHOT_BATCH_SIZE = 1000
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
        self.precomputed_service = PrecomputedAnalyticsService(session)
        self.snapshot_service = AnalyticsSnapshotService(session)

    @staticmethod
    def _snapshot_meta(*, status: str, last_updated: str | None, estimated_time: int | None = None) -> dict[str, str | int | bool | None]:
        return {
            "status": status,
            "last_updated": last_updated,
            "is_rebuilding": status == "pending",
            "estimated_time": estimated_time if status == "pending" else None,
        }

    @classmethod
    def _snapshot_status(cls, last_updated: str | None) -> str:
        if not last_updated:
            return "pending"
        try:
            parsed = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        except ValueError:
            return "ready"
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)
        return "stale" if age > cls.STALE_SNAPSHOT_THRESHOLD else "ready"

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
        precomputed = await self.precomputed_service.latest_tenant_dashboard(tenant_id=tenant_id)
        if precomputed is None:
            return {
                "tenant_id": tenant_id,
                "topic_mastery_distribution": {"beginner": 0, "needs_practice": 0, "mastered": 0},
                "diagnostic_completion_rate": 0.0,
                "roadmap_completion_rate": 0.0,
                "meta": self._snapshot_meta(
                    status="pending",
                    last_updated=None,
                    estimated_time=self.DEFAULT_REBUILD_ESTIMATED_TIME_SECONDS,
                ),
            }
        return {
            "tenant_id": tenant_id,
            "topic_mastery_distribution": dict(precomputed["topic_mastery_distribution"]),
            "diagnostic_completion_rate": float(precomputed["diagnostic_completion_rate"]),
            "roadmap_completion_rate": float(precomputed["roadmap_completion_rate"]),
            "meta": self._snapshot_meta(status=self._snapshot_status(precomputed.get("updated_at")), last_updated=precomputed.get("updated_at")),
        }

    async def topic_mastery_summary(self, tenant_id: int) -> dict:
        precomputed = await self.precomputed_service.latest_tenant_dashboard(tenant_id=tenant_id)
        return {
            "tenant_id": tenant_id,
            "topic_mastery_distribution": dict((precomputed or {}).get("topic_mastery_distribution") or {"beginner": 0, "needs_practice": 0, "mastered": 0}),
            "meta": self._snapshot_meta(
                status=self._snapshot_status((precomputed or {}).get("updated_at")) if precomputed is not None else "pending",
                last_updated=(precomputed or {}).get("updated_at"),
                estimated_time=self.DEFAULT_REBUILD_ESTIMATED_TIME_SECONDS if precomputed is None else None,
            ),
        }

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

        learners: list[dict[str, int | str]] = []
        offset = 0
        while True:
            result = await self.session.execute(stmt.limit(self.SNAPSHOT_BATCH_SIZE).offset(offset))
            rows = result.all()
            if not rows:
                break

            for row in rows:
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

            if len(rows) < self.SNAPSHOT_BATCH_SIZE:
                break
            offset += self.SNAPSHOT_BATCH_SIZE
        return learners

    async def roadmap_progress_summary(self, tenant_id: int, *, limit: int = 20, offset: int = 0) -> dict:
        snapshot = await self.snapshot_service.get_latest_snapshot(
            tenant_id,
            "roadmap_progress_summary",
        )
        payload = snapshot["data"] if snapshot is not None else None
        learners = list((payload or {}).get("learners") or [])
        total = len(learners)
        paginated_learners = learners[offset : offset + limit]
        if payload is not None:
            return {
                "tenant_id": tenant_id,
                "student_count": int(payload.get("student_count") or total),
                "average_completion_percent": int(payload.get("average_completion_percent") or 0),
                "average_mastery_percent": int(payload.get("average_mastery_percent") or 0),
                "learners": paginated_learners,
                "meta": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "next_offset": offset + limit if (offset + limit) < total else None,
                    "next_cursor": None,
                },
                "snapshot_meta": self._snapshot_meta(
                    status=self._snapshot_status(payload.get("updated_at") or (
                        snapshot["created_at"].isoformat() if snapshot.get("created_at") is not None else None
                    )),
                    last_updated=payload.get("updated_at") or (
                        snapshot["created_at"].isoformat() if snapshot.get("created_at") is not None else None
                    ),
                ),
            }
        return {
            "tenant_id": tenant_id,
            "student_count": 0,
            "average_completion_percent": 0,
            "average_mastery_percent": 0,
            "learners": [],
            "meta": {"total": 0, "limit": limit, "offset": offset, "next_offset": None, "next_cursor": None},
            "snapshot_meta": self._snapshot_meta(
                status="pending",
                last_updated=None,
                estimated_time=self.DEFAULT_REBUILD_ESTIMATED_TIME_SECONDS,
            ),
        }

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
        payload = await self.precomputed_service.latest_platform_overview()
        if payload is None:
            return {
                "tenant_count": 0,
                "student_count": 0,
                "mentor_count": 0,
                "teacher_count": 0,
                "admin_count": 0,
                "super_admin_count": 0,
                "diagnostic_completion_rate": 0.0,
                "roadmap_completion_rate": 0.0,
                "average_completion_percent": 0,
                "average_mastery_percent": 0,
                "topic_mastery_distribution": {"beginner": 0, "needs_practice": 0, "mastered": 0},
                "tenant_breakdown": [],
                "meta": self._snapshot_meta(
                    status="pending",
                    last_updated=None,
                    estimated_time=self.DEFAULT_REBUILD_ESTIMATED_TIME_SECONDS,
                ),
            }
        payload["meta"] = self._snapshot_meta(status=self._snapshot_status(payload.get("updated_at")), last_updated=payload.get("updated_at"))
        return payload

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
        payload = await self.precomputed_service.latest_student_performance_analytics(tenant_id=tenant_id, user_id=user_id)
        if payload is None:
            raise ValueError("Student analytics snapshot not ready")
        payload["meta"] = self._snapshot_meta(status=self._snapshot_status(payload.get("updated_at")), last_updated=payload.get("updated_at"))
        return payload

    @staticmethod
    def empty_student_performance_analytics(*, tenant_id: int, user_id: int) -> dict:
        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "learning_efficiency_score": 0.0,
            "topic_mastery_heatmap": [],
            "weak_topics": [],
            "performance_trend": [],
            "sql_queries": {},
            "meta": AnalyticsService._snapshot_meta(
                status="pending",
                last_updated=None,
                estimated_time=AnalyticsService.DEFAULT_REBUILD_ESTIMATED_TIME_SECONDS,
            ),
        }

    async def topic_performance_analytics(self, *, tenant_id: int, topic_id: int) -> dict:
        await self._require_tenant_topic(tenant_id=tenant_id, topic_id=topic_id)
        payload = await self.precomputed_service.latest_topic_performance_analytics(tenant_id=tenant_id, topic_id=topic_id)
        if payload is None:
            raise ValueError("Topic analytics snapshot not ready")
        payload["meta"] = self._snapshot_meta(status=self._snapshot_status(payload.get("updated_at")), last_updated=payload.get("updated_at"))
        return payload

    async def empty_topic_performance_analytics(self, *, tenant_id: int, topic_id: int) -> dict:
        await self._require_tenant_topic(tenant_id=tenant_id, topic_id=topic_id)
        topic = await self.topic_repository.get_topic(topic_id, tenant_id=tenant_id)
        return {
            "tenant_id": tenant_id,
            "topic_id": topic_id,
            "topic_name": getattr(topic, "name", f"Topic {topic_id}"),
            "learner_count": 0,
            "average_mastery_score": 0.0,
            "average_accuracy": 0.0,
            "average_time_taken_seconds": 0.0,
            "learning_efficiency_score": 0.0,
            "weakest_learners": [],
            "performance_trend": [],
            "sql_queries": {},
            "meta": self._snapshot_meta(
                status="pending",
                last_updated=None,
                estimated_time=self.DEFAULT_REBUILD_ESTIMATED_TIME_SECONDS,
            ),
        }
