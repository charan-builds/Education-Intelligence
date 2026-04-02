from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.outbox_service import OutboxService
from app.core.config import get_settings
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.repositories.analytics_snapshot_repository import AnalyticsSnapshotRepository
from app.infrastructure.repositories.tenant_scoping import tenant_user_scope
from app.domain.models.learning_event import LearningEvent
from app.domain.models.diagnostic_test import DiagnosticTest
from app.domain.models.question import Question
from app.domain.models.roadmap import Roadmap
from app.domain.models.roadmap_step import RoadmapStep
from app.domain.models.user_answer import UserAnswer
from app.domain.models.user_tenant_role import UserTenantRole
from app.domain.models.user import UserRole


class PrecomputedAnalyticsService:
    STUDENT_TOPIC_HEATMAP_SQL = """
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
ORDER BY mastery_score ASC, dt.user_id ASC
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
        self.repository = AnalyticsSnapshotRepository(session)
        self.cache = CacheService()

    async def _write_snapshot(
        self,
        *,
        tenant_id: int | None,
        snapshot_type: str,
        subject_id: int | None,
        payload: dict,
        window_start: datetime,
        window_end: datetime,
        updated_at: datetime,
    ) -> dict:
        row = await self.repository.create_snapshot_version(
            tenant_id=tenant_id,
            snapshot_type=snapshot_type,
            subject_id=subject_id,
            payload_json=json.dumps(payload, ensure_ascii=True),
            window_start=window_start,
            window_end=window_end,
            updated_at=updated_at,
        )
        payload["updated_at"] = row.updated_at.isoformat()
        payload["snapshot_version"] = int(row.snapshot_version)
        return payload

    @staticmethod
    def _attach_snapshot_metadata(payload: dict, snapshot) -> dict:
        payload["updated_at"] = snapshot.updated_at.isoformat()
        payload["snapshot_version"] = int(snapshot.snapshot_version)
        return payload

    async def prioritized_user_ids_for_refresh(self, *, tenant_id: int, limit: int) -> list[int]:
        if limit <= 0:
            return []
        recent_window_start = datetime.now(timezone.utc) - timedelta(days=7)
        rows = (
            await self.session.execute(
                select(
                    UserTenantRole.user_id,
                    func.max(func.coalesce(LearningEvent.event_timestamp, LearningEvent.created_at)).label("last_activity_at"),
                    func.count(LearningEvent.id).label("activity_count"),
                )
                .select_from(UserTenantRole)
                .outerjoin(
                    LearningEvent,
                    (LearningEvent.tenant_id == UserTenantRole.tenant_id)
                    & (LearningEvent.user_id == UserTenantRole.user_id)
                    & (func.coalesce(LearningEvent.event_timestamp, LearningEvent.created_at) >= recent_window_start),
                )
                .where(
                    UserTenantRole.tenant_id == tenant_id,
                    UserTenantRole.role == UserRole.student,
                )
                .group_by(UserTenantRole.user_id)
                .order_by(
                    func.max(func.coalesce(LearningEvent.event_timestamp, LearningEvent.created_at)).desc().nullslast(),
                    func.count(LearningEvent.id).desc(),
                    UserTenantRole.user_id.asc(),
                )
                .limit(limit)
            )
        ).all()
        return [int(row.user_id) for row in rows]

    async def refresh_priority_user_batch(self, *, tenant_id: int, limit_users: int = 50) -> dict:
        user_ids = await self.prioritized_user_ids_for_refresh(tenant_id=tenant_id, limit=limit_users)
        refreshed_users = 0
        refreshed_student_analytics = 0
        for user_id in user_ids:
            await self.refresh_user_learning_summary(tenant_id=tenant_id, user_id=user_id)
            await self.refresh_user_diagnostic_summary(tenant_id=tenant_id, user_id=user_id)
            await self.refresh_user_roadmap_stats(tenant_id=tenant_id, user_id=user_id)
            await self.refresh_student_performance_analytics(tenant_id=tenant_id, user_id=user_id)
            refreshed_users += 1
            refreshed_student_analytics += 1
        return {
            "tenant_id": tenant_id,
            "refreshed_users": refreshed_users,
            "refreshed_student_analytics": refreshed_student_analytics,
            "prioritized_user_ids": user_ids,
        }

    @staticmethod
    def _compute_learning_efficiency(*, average_accuracy: float, average_time_taken_seconds: float, average_attempts: float) -> float:
        normalized_accuracy = max(0.0, min(100.0, float(average_accuracy)))
        speed_component = max(0.0, 100.0 - (min(float(average_time_taken_seconds), 120.0) / 120.0 * 100.0))
        attempts_component = max(0.0, 100.0 - (max(float(average_attempts) - 1.0, 0.0) * 35.0))
        return round((normalized_accuracy * 0.55) + (speed_component * 0.3) + (attempts_component * 0.15), 2)

    async def refresh_materialized_views(self) -> None:
        dialect = str(self.session.bind.dialect.name if self.session.bind is not None else "")
        if dialect != "postgresql":
            return
        await self.session.execute(text("REFRESH MATERIALIZED VIEW tenant_analytics_mv"))
        await self.session.execute(text("REFRESH MATERIALIZED VIEW user_progress_summary_mv"))

    async def tenant_dashboard_from_materialized_view(self, *, tenant_id: int) -> dict | None:
        dialect = str(self.session.bind.dialect.name if self.session.bind is not None else "")
        if dialect != "postgresql":
            return None
        row = (
            await self.session.execute(
                text(
                    """
                    SELECT
                        tenant_id,
                        active_learners,
                        weekly_event_count,
                        average_topic_mastery,
                        diagnostic_completion_rate,
                        roadmap_completion_rate,
                        beginner_topics,
                        needs_practice_topics,
                        mastered_topics,
                        refreshed_at
                    FROM tenant_analytics_mv
                    WHERE tenant_id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id},
            )
        ).mappings().one_or_none()
        if row is None:
            return None
        return {
            "tenant_id": int(row["tenant_id"]),
            "active_learners": int(row["active_learners"] or 0),
            "weekly_event_count": int(row["weekly_event_count"] or 0),
            "average_topic_mastery": round(float(row["average_topic_mastery"] or 0.0), 2),
            "diagnostic_completion_rate": round(float(row["diagnostic_completion_rate"] or 0.0), 2),
            "roadmap_completion_rate": round(float(row["roadmap_completion_rate"] or 0.0), 2),
            "topic_mastery_distribution": {
                "beginner": int(row["beginner_topics"] or 0),
                "needs_practice": int(row["needs_practice_topics"] or 0),
                "mastered": int(row["mastered_topics"] or 0),
            },
            "updated_at": row["refreshed_at"].isoformat() if row["refreshed_at"] is not None else None,
        }

    async def roadmap_progress_from_materialized_view(self, *, tenant_id: int, limit: int = 20, offset: int = 0) -> dict | None:
        dialect = str(self.session.bind.dialect.name if self.session.bind is not None else "")
        if dialect != "postgresql":
            return None
        count_row = (
            await self.session.execute(
                text("SELECT COUNT(*) AS total FROM user_progress_summary_mv WHERE tenant_id = :tenant_id"),
                {"tenant_id": tenant_id},
            )
        ).mappings().one()
        total = int(count_row["total"] or 0)
        rows = (
            await self.session.execute(
                text(
                    """
                    SELECT
                        user_id,
                        email,
                        total_steps,
                        completed_steps,
                        in_progress_steps,
                        pending_steps,
                        completion_percent,
                        mastery_percent
                    FROM user_progress_summary_mv
                    WHERE tenant_id = :tenant_id
                    ORDER BY mastery_percent DESC, completion_percent DESC, email ASC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {"tenant_id": tenant_id, "limit": limit, "offset": offset},
            )
        ).mappings().all()
        summary = (
            await self.session.execute(
                text(
                    """
                    SELECT
                        COALESCE(ROUND(AVG(completion_percent)), 0) AS average_completion_percent,
                        COALESCE(ROUND(AVG(mastery_percent)), 0) AS average_mastery_percent
                    FROM user_progress_summary_mv
                    WHERE tenant_id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id},
            )
        ).mappings().one()
        return {
            "tenant_id": tenant_id,
            "student_count": total,
            "average_completion_percent": int(summary["average_completion_percent"] or 0),
            "average_mastery_percent": int(summary["average_mastery_percent"] or 0),
            "learners": [
                {
                    "user_id": int(row["user_id"]),
                    "email": str(row["email"]),
                    "total_steps": int(row["total_steps"] or 0),
                    "completed_steps": int(row["completed_steps"] or 0),
                    "in_progress_steps": int(row["in_progress_steps"] or 0),
                    "pending_steps": int(row["pending_steps"] or 0),
                    "completion_percent": int(row["completion_percent"] or 0),
                    "mastery_percent": int(row["mastery_percent"] or 0),
                }
                for row in rows
            ],
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": offset + limit if (offset + limit) < total else None,
                "next_cursor": None,
            },
        }

    async def refresh_tenant_dashboard(self, *, tenant_id: int) -> dict:
        mv_payload = await self.tenant_dashboard_from_materialized_view(tenant_id=tenant_id)
        if mv_payload is not None:
            payload = {
                "tenant_id": int(mv_payload["tenant_id"]),
                "active_learners": int(mv_payload["active_learners"]),
                "weekly_event_count": int(mv_payload["weekly_event_count"]),
                "average_topic_mastery": round(float(mv_payload["average_topic_mastery"]), 2),
                "diagnostic_completion_rate": round(float(mv_payload["diagnostic_completion_rate"]), 2),
                "roadmap_completion_rate": round(float(mv_payload["roadmap_completion_rate"]), 2),
                "topic_mastery_distribution": dict(mv_payload["topic_mastery_distribution"]),
            }
            now = datetime.now(timezone.utc)
            window_start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
            payload = await self._write_snapshot(
                tenant_id=tenant_id,
                snapshot_type="tenant_dashboard",
                subject_id=None,
                payload=payload,
                window_start=window_start,
                window_end=now,
                updated_at=now,
            )
            cache_key = await self.cache.build_tenant_versioned_key("analytics:precomputed:tenant-dashboard", tenant_id=tenant_id)
            await self.cache.set(cache_key, payload, ttl=300)
            return payload
        now = datetime.now(timezone.utc)
        window_start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        active_learners = int(
            (
                await self.session.execute(
                    select(func.count(UserTenantRole.id)).where(
                        UserTenantRole.tenant_id == tenant_id,
                        UserTenantRole.role == UserRole.student,
                    )
                )
            ).scalar_one()
            or 0
        )
        event_count = int(
            (
                await self.session.execute(
                    select(func.count(LearningEvent.id)).where(
                        LearningEvent.tenant_id == tenant_id,
                        func.coalesce(LearningEvent.event_timestamp, LearningEvent.created_at) >= window_start,
                    )
                )
            ).scalar_one()
            or 0
        )
        # Current state only: compute topic mastery from the latest completed diagnostic test per user.
        current_tests = (
            select(DiagnosticTest.user_id.label("user_id"), func.max(DiagnosticTest.id).label("test_id"))
            .join(DiagnosticTest.user)
            .where(DiagnosticTest.completed_at.is_not(None))
            .where(tenant_user_scope(DiagnosticTest.user, tenant_id))
            .group_by(DiagnosticTest.user_id)
        ).subquery()

        topic_avg_subq = (
            select(Question.topic_id.label("topic_id"), func.avg(UserAnswer.score).label("topic_avg"))
            .select_from(current_tests)
            .join(UserAnswer, UserAnswer.test_id == current_tests.c.test_id)
            .join(Question, Question.id == UserAnswer.question_id)
            .group_by(Question.topic_id)
        ).subquery()

        avg_mastery = float((await self.session.execute(select(func.avg(topic_avg_subq.c.topic_avg)))).scalar_one() or 0.0)
        payload = {
            "tenant_id": tenant_id,
            "active_learners": active_learners,
            "weekly_event_count": event_count,
            "average_topic_mastery": round(avg_mastery, 2),
        }
        payload = await self._write_snapshot(
            tenant_id=tenant_id,
            snapshot_type="tenant_dashboard",
            subject_id=None,
            payload=payload,
            window_start=window_start,
            window_end=now,
            updated_at=now,
        )
        cache_key = await self.cache.build_tenant_versioned_key("analytics:precomputed:tenant-dashboard", tenant_id=tenant_id)
        await self.cache.set(cache_key, payload, ttl=300)
        if get_settings().kafka_enabled:
            await OutboxService(self.session).add_analytics_message(
                tenant_id=tenant_id,
                snapshot_type="tenant_dashboard",
                subject_id=None,
                window_start=window_start.isoformat(),
                window_end=now.isoformat(),
                idempotency_key=f"analytics:{tenant_id}:tenant_dashboard:{window_start.date().isoformat()}",
            )
        return payload

    async def latest_tenant_dashboard(self, *, tenant_id: int) -> dict | None:
        snapshot = await self.repository.latest_snapshot(
            tenant_id=tenant_id,
            snapshot_type="tenant_dashboard",
            subject_id=None,
        )
        if snapshot is None:
            return None
        payload = json.loads(snapshot.payload_json)
        payload["window_start"] = snapshot.window_start.isoformat()
        payload["window_end"] = snapshot.window_end.isoformat()
        return self._attach_snapshot_metadata(payload, snapshot)

    async def refresh_user_learning_summary(self, *, tenant_id: int, user_id: int) -> dict:
        now = datetime.now(timezone.utc)
        window_start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        event_count = int(
            (
                await self.session.execute(
                    select(func.count(LearningEvent.id)).where(
                        LearningEvent.tenant_id == tenant_id,
                        LearningEvent.user_id == user_id,
                        func.coalesce(LearningEvent.event_timestamp, LearningEvent.created_at) >= window_start,
                    )
                )
            ).scalar_one()
            or 0
        )
        # Current state only: compute summary from the latest completed diagnostic answers for this user.
        latest_test_id_subq = (
            select(func.max(DiagnosticTest.id))
            .select_from(DiagnosticTest)
            .where(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.completed_at.is_not(None),
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
        ).scalar_subquery()

        avg_score = float(
            (
                await self.session.execute(
                    select(func.avg(UserAnswer.score))
                    .join(DiagnosticTest, DiagnosticTest.id == UserAnswer.test_id)
                    .where(
                        DiagnosticTest.user_id == user_id,
                        DiagnosticTest.completed_at.is_not(None),
                        DiagnosticTest.id == latest_test_id_subq,
                        tenant_user_scope(DiagnosticTest.user, tenant_id),
                    )
                )
            ).scalar_one()
            or 0.0
        )
        payload = {"tenant_id": tenant_id, "user_id": user_id, "weekly_event_count": event_count, "average_score": round(avg_score, 2)}
        payload = await self._write_snapshot(
            tenant_id=tenant_id,
            snapshot_type="user_learning_summary",
            subject_id=user_id,
            payload=payload,
            window_start=window_start,
            window_end=now,
            updated_at=now,
        )
        if get_settings().kafka_enabled:
            await OutboxService(self.session).add_analytics_message(
                tenant_id=tenant_id,
                snapshot_type="user_learning_summary",
                subject_id=user_id,
                window_start=window_start.isoformat(),
                window_end=now.isoformat(),
                idempotency_key=f"analytics:{tenant_id}:user_learning_summary:{user_id}:{window_start.date().isoformat()}",
            )
        return payload

    async def latest_user_learning_summary(self, *, tenant_id: int, user_id: int) -> dict | None:
        snapshot = await self.repository.latest_snapshot(
            tenant_id=tenant_id,
            snapshot_type="user_learning_summary",
            subject_id=user_id,
        )
        if snapshot is None:
            return None
        payload = json.loads(snapshot.payload_json)
        payload["window_start"] = snapshot.window_start.isoformat()
        payload["window_end"] = snapshot.window_end.isoformat()
        return self._attach_snapshot_metadata(payload, snapshot)

    async def refresh_student_performance_analytics(self, *, tenant_id: int, user_id: int) -> dict:
        now = datetime.now(timezone.utc)
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
        payload = {
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
        return await self._write_snapshot(
            tenant_id=tenant_id,
            snapshot_type="student_performance_analytics",
            subject_id=user_id,
            payload=payload,
            window_start=now,
            window_end=now,
            updated_at=now,
        )

    async def latest_student_performance_analytics(self, *, tenant_id: int, user_id: int) -> dict | None:
        snapshot = await self.repository.latest_snapshot(
            tenant_id=tenant_id,
            snapshot_type="student_performance_analytics",
            subject_id=user_id,
        )
        if snapshot is None:
            return None
        payload = json.loads(snapshot.payload_json)
        return self._attach_snapshot_metadata(payload, snapshot)

    async def refresh_topic_performance_analytics(self, *, tenant_id: int, topic_id: int, topic_name: str) -> dict:
        now = datetime.now(timezone.utc)
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
        average_time_taken_seconds = round(sum(item["average_time_taken_seconds"] for item in weakest_learners) / learner_count, 2) if weakest_learners else 0.0
        average_attempts = round(sum(item["average_attempts"] for item in weakest_learners) / learner_count, 2) if weakest_learners else 1.0
        payload = {
            "tenant_id": tenant_id,
            "topic_id": int(topic_id),
            "topic_name": str(topic_name),
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
        return await self._write_snapshot(
            tenant_id=tenant_id,
            snapshot_type="topic_performance_analytics",
            subject_id=topic_id,
            payload=payload,
            window_start=now,
            window_end=now,
            updated_at=now,
        )

    async def latest_topic_performance_analytics(self, *, tenant_id: int, topic_id: int) -> dict | None:
        snapshot = await self.repository.latest_snapshot(
            tenant_id=tenant_id,
            snapshot_type="topic_performance_analytics",
            subject_id=topic_id,
        )
        if snapshot is None:
            return None
        payload = json.loads(snapshot.payload_json)
        return self._attach_snapshot_metadata(payload, snapshot)

    async def refresh_platform_overview(self) -> dict:
        await self.refresh_materialized_views()
        now = datetime.now(timezone.utc)
        dialect = str(self.session.bind.dialect.name if self.session.bind is not None else "")
        tenant_breakdown: list[dict] = []
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
                            t.id, t.name, t.type,
                            tam.diagnostic_completion_rate, tam.roadmap_completion_rate,
                            tam.beginner_topics, tam.needs_practice_topics, tam.mastered_topics,
                            ups.average_completion_percent, ups.average_mastery_percent
                        ORDER BY t.name ASC
                        """
                    )
                )
            ).mappings().all()
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
                    "beginner_topics": int(row["beginner_topics"] or 0),
                    "needs_practice_topics": int(row["needs_practice_topics"] or 0),
                    "mastered_topics": int(row["mastered_topics"] or 0),
                }
                for row in tenant_rows
            ]
        payload = {
            "tenant_count": len(tenant_breakdown),
            "student_count": sum(int(item["student_count"]) for item in tenant_breakdown),
            "mentor_count": sum(int(item["mentor_count"]) for item in tenant_breakdown),
            "teacher_count": sum(int(item["teacher_count"]) for item in tenant_breakdown),
            "admin_count": sum(int(item["admin_count"]) for item in tenant_breakdown),
            "super_admin_count": sum(int(item["super_admin_count"]) for item in tenant_breakdown),
            "diagnostic_completion_rate": round(sum(float(item["diagnostic_completion_rate"]) for item in tenant_breakdown) / max(len(tenant_breakdown), 1), 2) if tenant_breakdown else 0.0,
            "roadmap_completion_rate": round(sum(float(item["roadmap_completion_rate"]) for item in tenant_breakdown) / max(len(tenant_breakdown), 1), 2) if tenant_breakdown else 0.0,
            "average_completion_percent": round(sum(int(item["average_completion_percent"]) for item in tenant_breakdown) / max(len(tenant_breakdown), 1)) if tenant_breakdown else 0,
            "average_mastery_percent": round(sum(int(item["average_mastery_percent"]) for item in tenant_breakdown) / max(len(tenant_breakdown), 1)) if tenant_breakdown else 0,
            "topic_mastery_distribution": {
                "beginner": sum(int(item.get("beginner_topics", 0)) for item in tenant_breakdown),
                "needs_practice": sum(int(item.get("needs_practice_topics", 0)) for item in tenant_breakdown),
                "mastered": sum(int(item.get("mastered_topics", 0)) for item in tenant_breakdown),
            },
            "tenant_breakdown": [
                {
                    "tenant_id": item["tenant_id"],
                    "tenant_name": item["tenant_name"],
                    "tenant_type": item["tenant_type"],
                    "student_count": item["student_count"],
                    "mentor_count": item["mentor_count"],
                    "teacher_count": item["teacher_count"],
                    "admin_count": item["admin_count"],
                    "super_admin_count": item["super_admin_count"],
                    "diagnostic_completion_rate": item["diagnostic_completion_rate"],
                    "roadmap_completion_rate": item["roadmap_completion_rate"],
                    "average_completion_percent": item["average_completion_percent"],
                    "average_mastery_percent": item["average_mastery_percent"],
                }
                for item in tenant_breakdown
            ],
        }
        return await self._write_snapshot(
            tenant_id=None,
            snapshot_type="platform_overview",
            subject_id=None,
            payload=payload,
            window_start=now,
            window_end=now,
            updated_at=now,
        )

    async def latest_platform_overview(self) -> dict | None:
        snapshot = await self.repository.latest_snapshot(tenant_id=None, snapshot_type="platform_overview", subject_id=None)
        if snapshot is None:
            return None
        payload = json.loads(snapshot.payload_json)
        return self._attach_snapshot_metadata(payload, snapshot)

    async def refresh_user_diagnostic_summary(self, *, tenant_id: int, user_id: int) -> dict:
        now = datetime.now(timezone.utc)
        latest_test = await self.session.scalar(
            select(DiagnosticTest)
            .where(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.completed_at.is_not(None),
                tenant_user_scope(DiagnosticTest.user, tenant_id),
            )
            .order_by(DiagnosticTest.completed_at.desc(), DiagnosticTest.id.desc())
            .limit(1)
        )
        latest_test_id = int(latest_test.id) if latest_test is not None and latest_test.id is not None else None
        average_score = 0.0
        answered_questions = 0
        weak_topic_count = 0
        if latest_test_id is not None:
            average_score = round(
                float(
                    (
                        await self.session.execute(
                            select(func.avg(UserAnswer.score)).where(UserAnswer.test_id == latest_test_id)
                        )
                    ).scalar_one()
                    or 0.0
                ),
                2,
            )
            answered_questions = int(
                (
                    await self.session.execute(
                        select(func.count(UserAnswer.id)).where(UserAnswer.test_id == latest_test_id)
                    )
                ).scalar_one()
                or 0
            )
            topic_scores = (
                await self.session.execute(
                    select(Question.topic_id, func.avg(UserAnswer.score))
                    .join(Question, Question.id == UserAnswer.question_id)
                    .where(UserAnswer.test_id == latest_test_id)
                    .group_by(Question.topic_id)
                )
            ).all()
            weak_topic_count = sum(1 for _, avg_score in topic_scores if float(avg_score or 0.0) < 70.0)

        payload = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "latest_test_id": latest_test_id,
            "average_score": average_score,
            "answered_questions": answered_questions,
            "weak_topic_count": weak_topic_count,
        }
        return await self._write_snapshot(
            tenant_id=tenant_id,
            snapshot_type="user_diagnostic_summary",
            subject_id=user_id,
            payload=payload,
            window_start=now,
            window_end=now,
            updated_at=now,
        )

    async def refresh_user_roadmap_stats(self, *, tenant_id: int, user_id: int) -> dict:
        now = datetime.now(timezone.utc)
        roadmap = await self.session.scalar(
            select(Roadmap)
            .where(Roadmap.user_id == user_id)
            .order_by(Roadmap.generated_at.desc().nullslast(), Roadmap.id.desc())
            .limit(1)
        )
        roadmap_id = int(roadmap.id) if roadmap is not None and roadmap.id is not None else None
        total_steps = 0
        completed_steps = 0
        in_progress_steps = 0
        pending_steps = 0
        completion_percent = 0
        if roadmap_id is not None:
            step_rows = (
                await self.session.execute(
                    select(RoadmapStep.progress_status).where(RoadmapStep.roadmap_id == roadmap_id)
                )
            ).all()
            total_steps = len(step_rows)
            for (status,) in step_rows:
                normalized = str(status or "pending").strip().lower()
                if normalized == "completed":
                    completed_steps += 1
                elif normalized == "in_progress":
                    in_progress_steps += 1
                else:
                    pending_steps += 1
            completion_percent = int(round((completed_steps / total_steps) * 100)) if total_steps else 0

        payload = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "roadmap_id": roadmap_id,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "in_progress_steps": in_progress_steps,
            "pending_steps": pending_steps,
            "completion_percent": completion_percent,
        }
        return await self._write_snapshot(
            tenant_id=tenant_id,
            snapshot_type="user_roadmap_stats",
            subject_id=user_id,
            payload=payload,
            window_start=now,
            window_end=now,
            updated_at=now,
        )

    async def refresh_scheduled_tenant_projections(self, *, tenant_id: int, limit_users: int = 250) -> dict:
        tenant_dashboard = await self.refresh_tenant_dashboard(tenant_id=tenant_id)
        batch_result = await self.refresh_priority_user_batch(
            tenant_id=tenant_id,
            limit_users=min(limit_users, 50),
        )
        return {
            "tenant_dashboard": tenant_dashboard,
            "refreshed_users": int(batch_result["refreshed_users"]),
            "refreshed_student_analytics": int(batch_result["refreshed_student_analytics"]),
            "tenant_id": tenant_id,
        }

    async def refresh_bundle(self, *, tenant_id: int, user_id: int | None = None, limit_users: int = 250) -> dict:
        await self.refresh_materialized_views()
        tenant_dashboard = await self.refresh_tenant_dashboard(tenant_id=tenant_id)
        refreshed_users = 0
        refreshed_student_analytics = 0
        if user_id is not None:
            await self.refresh_user_learning_summary(tenant_id=tenant_id, user_id=user_id)
            await self.refresh_user_diagnostic_summary(tenant_id=tenant_id, user_id=user_id)
            await self.refresh_user_roadmap_stats(tenant_id=tenant_id, user_id=user_id)
            await self.refresh_student_performance_analytics(tenant_id=tenant_id, user_id=user_id)
            refreshed_users = 1
            refreshed_student_analytics = 1
        else:
            batch_result = await self.refresh_priority_user_batch(
                tenant_id=tenant_id,
                limit_users=min(limit_users, 50),
            )
            refreshed_users = int(batch_result["refreshed_users"])
            refreshed_student_analytics = int(batch_result["refreshed_student_analytics"])
        return {
            "tenant_dashboard": tenant_dashboard,
            "refreshed_users": refreshed_users,
            "refreshed_student_analytics": refreshed_student_analytics,
            "tenant_id": tenant_id,
        }
