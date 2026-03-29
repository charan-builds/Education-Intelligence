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
from app.domain.models.user_answer import UserAnswer
from app.domain.models.user_tenant_role import UserTenantRole
from app.domain.models.user import UserRole


class PrecomputedAnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = AnalyticsSnapshotRepository(session)
        self.cache = CacheService()

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
            await self.repository.upsert_snapshot(
                tenant_id=tenant_id,
                snapshot_type="tenant_dashboard",
                subject_id=None,
                payload_json=json.dumps(payload, ensure_ascii=True),
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
        await self.repository.upsert_snapshot(
            tenant_id=tenant_id,
            snapshot_type="tenant_dashboard",
            subject_id=None,
            payload_json=json.dumps(payload, ensure_ascii=True),
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
        payload["updated_at"] = snapshot.updated_at.isoformat()
        return payload

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
        await self.repository.upsert_snapshot(
            tenant_id=tenant_id,
            snapshot_type="user_learning_summary",
            subject_id=user_id,
            payload_json=json.dumps(payload, ensure_ascii=True),
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
        payload["updated_at"] = snapshot.updated_at.isoformat()
        return payload

    async def refresh_bundle(self, *, tenant_id: int, user_id: int | None = None, limit_users: int = 250) -> dict:
        await self.refresh_materialized_views()
        tenant_dashboard = await self.refresh_tenant_dashboard(tenant_id=tenant_id)
        refreshed_users = 0
        if user_id is not None:
            await self.refresh_user_learning_summary(tenant_id=tenant_id, user_id=user_id)
            refreshed_users = 1
        else:
            user_rows = (
                await self.session.execute(
                    select(UserTenantRole.user_id)
                    .where(
                        UserTenantRole.tenant_id == tenant_id,
                        UserTenantRole.role == UserRole.student,
                    )
                    .order_by(UserTenantRole.user_id.asc())
                    .limit(limit_users)
                )
            ).all()
            for row in user_rows:
                await self.refresh_user_learning_summary(tenant_id=tenant_id, user_id=int(row.user_id))
                refreshed_users += 1
        return {
            "tenant_dashboard": tenant_dashboard,
            "refreshed_users": refreshed_users,
            "tenant_id": tenant_id,
        }
