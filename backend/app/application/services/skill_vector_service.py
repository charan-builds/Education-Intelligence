from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.learning_event import LearningEvent
from app.domain.models.topic import Topic
from app.domain.models.user_skill_vector import UserSkillVector
from app.infrastructure.repositories.user_skill_vector_repository import UserSkillVectorRepository


class SkillVectorService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = UserSkillVectorRepository(session)

    async def update_from_diagnostic_answer(
        self,
        *,
        tenant_id: int,
        user_id: int,
        topic_id: int,
        score: float,
        time_taken_seconds: float,
        answered_at: datetime | None = None,
    ) -> dict:
        current = await self.repository.get_for_user_topic(tenant_id=tenant_id, user_id=user_id, topic_id=topic_id)
        previous_mastery = float(current.mastery_score if current is not None else 0.0)
        previous_confidence = float(current.confidence_score if current is not None else 0.0)
        normalized_score = max(0.0, min(100.0, float(score)))
        speed_bonus = max(0.0, min(1.0, 1.0 - (float(time_taken_seconds) / 180.0)))
        next_mastery = round((previous_mastery * 0.65) + (normalized_score * 0.35), 2)
        next_confidence = round(min(1.0, (previous_confidence * 0.7) + (0.2 + (speed_bonus * 0.1))), 4)
        at = answered_at or datetime.now(timezone.utc)
        row = await self.repository.upsert(
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=topic_id,
            mastery_score=next_mastery,
            confidence_score=next_confidence,
            last_updated=at,
        )
        return {
            "topic_id": row.topic_id,
            "mastery_score": row.mastery_score,
            "confidence_score": row.confidence_score,
        }

    async def update_from_progress(
        self,
        *,
        tenant_id: int,
        user_id: int,
        topic_id: int,
        progress_status: str,
        observed_at: datetime | None = None,
    ) -> dict:
        current = await self.repository.get_for_user_topic(tenant_id=tenant_id, user_id=user_id, topic_id=topic_id)
        previous_mastery = float(current.mastery_score if current is not None else 0.0)
        previous_confidence = float(current.confidence_score if current is not None else 0.0)
        status = progress_status.strip().lower()
        mastery_boost = {"pending": 0.0, "in_progress": 7.5, "completed": 18.0}.get(status, 0.0)
        confidence_boost = {"pending": 0.0, "in_progress": 0.05, "completed": 0.12}.get(status, 0.0)
        at = observed_at or datetime.now(timezone.utc)
        row = await self.repository.upsert(
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=topic_id,
            mastery_score=round(min(100.0, previous_mastery + mastery_boost), 2),
            confidence_score=round(min(1.0, previous_confidence + confidence_boost), 4),
            last_updated=at,
        )
        return {
            "topic_id": row.topic_id,
            "mastery_score": row.mastery_score,
            "confidence_score": row.confidence_score,
        }

    async def decay_inactive_vectors(
        self,
        *,
        tenant_id: int | None = None,
        inactive_days: int = 21,
        decay_factor: float = 0.97,
    ) -> int:
        threshold = datetime.now(timezone.utc) - timedelta(days=inactive_days)
        stmt_vectors = select(UserSkillVector).where(UserSkillVector.last_updated < threshold)
        if tenant_id is not None:
            stmt_vectors = stmt_vectors.where(UserSkillVector.tenant_id == tenant_id)
        vectors = list((await self.session.execute(stmt_vectors)).scalars().all())
        for row in vectors:
            row.mastery_score = round(max(0.0, row.mastery_score * decay_factor), 2)
            row.confidence_score = round(max(0.0, row.confidence_score * 0.98), 4)
            row.last_updated = datetime.now(timezone.utc)
        await self.session.commit()
        return len(vectors)

    async def topic_mastery_distribution(self, *, tenant_id: int) -> dict[str, int]:
        buckets = {"beginner": 0, "needs_practice": 0, "mastered": 0}
        rows = list(
            (
                await self.session.execute(
                    select(UserSkillVector.mastery_score).where(UserSkillVector.tenant_id == tenant_id)
                )
            ).scalars().all()
        )
        for mastery in rows:
            if mastery < 50:
                buckets["beginner"] += 1
            elif mastery <= 75:
                buckets["needs_practice"] += 1
            else:
                buckets["mastered"] += 1
        return buckets

    async def weak_topics(self, *, tenant_id: int, user_id: int | None = None, limit: int = 8) -> list[dict]:
        stmt = (
            select(UserSkillVector.topic_id, Topic.name, UserSkillVector.mastery_score, UserSkillVector.confidence_score)
            .join(Topic, Topic.id == UserSkillVector.topic_id)
            .where(UserSkillVector.tenant_id == tenant_id)
            .order_by(UserSkillVector.mastery_score.asc(), UserSkillVector.confidence_score.asc())
            .limit(limit)
        )
        if user_id is not None:
            stmt = stmt.where(UserSkillVector.user_id == user_id)
        rows = (await self.session.execute(stmt)).all()
        return [
            {
                "topic_id": int(topic_id),
                "topic_name": topic_name,
                "mastery_score": round(float(mastery_score), 2),
                "confidence_score": round(float(confidence_score), 4),
            }
            for topic_id, topic_name, mastery_score, confidence_score in rows
        ]

    async def learner_vectors(self, *, tenant_id: int, user_id: int) -> list[dict]:
        rows = await self.repository.list_for_user(tenant_id=tenant_id, user_id=user_id)
        topic_ids = [row.topic_id for row in rows]
        names = {}
        if topic_ids:
            topic_rows = (
                await self.session.execute(select(Topic.id, Topic.name).where(Topic.id.in_(topic_ids), Topic.tenant_id == tenant_id))
            ).all()
            names = {int(topic_id): str(name) for topic_id, name in topic_rows}
        return [
            {
                "topic_id": row.topic_id,
                "topic_name": names.get(row.topic_id, f"Topic {row.topic_id}"),
                "mastery_score": round(float(row.mastery_score), 2),
                "confidence_score": round(float(row.confidence_score), 4),
                "last_updated": row.last_updated.isoformat(),
            }
            for row in rows
        ]

    async def learning_trends(self, *, tenant_id: int, days: int = 14) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        rows = (
            await self.session.execute(
                select(LearningEvent.event_timestamp, LearningEvent.action_type, LearningEvent.time_spent_seconds)
                .where(
                    LearningEvent.tenant_id == tenant_id,
                    func.coalesce(LearningEvent.event_timestamp, LearningEvent.created_at) >= since,
                )
                .order_by(func.coalesce(LearningEvent.event_timestamp, LearningEvent.created_at).asc())
            )
        ).all()
        trend: dict[str, dict[str, float | int | str]] = {}
        for ts, action_type, time_spent_seconds in rows:
            if ts is None:
                continue
            label = ts.date().isoformat()
            bucket = trend.setdefault(
                label,
                {"label": label, "events": 0, "minutes_spent": 0.0, "completions": 0, "retries": 0},
            )
            bucket["events"] = int(bucket["events"]) + 1
            bucket["minutes_spent"] = round(float(bucket["minutes_spent"]) + (float(time_spent_seconds or 0) / 60.0), 2)
            if action_type == "complete":
                bucket["completions"] = int(bucket["completions"]) + 1
            if action_type == "retry":
                bucket["retries"] = int(bucket["retries"]) + 1
        return [trend[key] for key in sorted(trend.keys())]

    async def aggregated_feature_payload(self, *, tenant_id: int, user_id: int) -> dict:
        rows = await self.learner_vectors(tenant_id=tenant_id, user_id=user_id)
        mastery_avg = round(sum(row["mastery_score"] for row in rows) / max(len(rows), 1), 2) if rows else 0.0
        confidence_avg = round(sum(row["confidence_score"] for row in rows) / max(len(rows), 1), 4) if rows else 0.0
        recent_retry_count = int(
            (
                await self.session.execute(
                    select(func.count(LearningEvent.id)).where(
                        LearningEvent.tenant_id == tenant_id,
                        LearningEvent.user_id == user_id,
                        LearningEvent.action_type == "retry",
                    )
                )
            ).scalar_one()
            or 0
        )
        average_speed = (
            await self.session.execute(
                select(func.avg(LearningEvent.time_spent_seconds)).where(
                    LearningEvent.tenant_id == tenant_id,
                    LearningEvent.user_id == user_id,
                    LearningEvent.time_spent_seconds.is_not(None),
                )
            )
        ).scalar_one()
        return {
            "mastery_avg": mastery_avg,
            "confidence_avg": confidence_avg,
            "learning_speed_seconds": round(float(average_speed or 0.0), 2),
            "retry_count": recent_retry_count,
            "tracked_topics": len(rows),
        }
