from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.learning_event import LearningEvent
from app.domain.models.resource import Resource
from app.domain.models.topic import Topic
from app.domain.models.topic_score import TopicScore


class RetentionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _interval_from_score(score: float) -> int:
        if score >= 85:
            return 10
        if score >= 75:
            return 7
        if score >= 60:
            return 4
        return 2

    @staticmethod
    def _retention_from_score(*, score: float, days_since_review: int, previous_interval_days: int = 1) -> float:
        base_strength = max(0.2, min(1.0, float(score) / 100.0))
        stability = max(1.0, float(previous_interval_days))
        retention = base_strength * (2.718281828 ** (-(float(days_since_review) / stability)))
        return round(max(0.08, min(1.0, retention)), 3)

    def schedule_plan(
        self,
        *,
        score: float,
        mastery_delta: float = 0.0,
        confidence: float = 0.6,
        days_since_review: int = 0,
        previous_interval_days: int = 1,
        performed_well: bool | None = None,
    ) -> dict:
        retention_score = self._retention_from_score(
            score=score,
            days_since_review=days_since_review,
            previous_interval_days=previous_interval_days,
        )
        urgency = ((100.0 - score) * 0.45) + (max(0.0, -mastery_delta) * 1.1) + ((1.0 - confidence) * 28.0) + (days_since_review * 2.4)
        interval = max(
            1,
            self._interval_from_score(score)
            - (1 if urgency > 35 else 0)
            - (1 if retention_score < 0.45 else 0),
        )
        if performed_well is True:
            interval = max(interval, int(round(previous_interval_days * 1.8)))
        elif performed_well is False:
            interval = max(1, min(interval, int(round(previous_interval_days * 0.7)) or 1))
        return {
            "review_interval_days": interval,
            "revision_interval_days": interval,
            "retention_score": retention_score,
            "review_due_at": datetime.now(timezone.utc) + timedelta(days=interval),
            "urgency_score": round(max(0.0, min(100.0, urgency)), 2),
        }

    async def upsert_topic_score(
        self,
        *,
        tenant_id: int,
        user_id: int,
        topic_id: int,
        score: float,
        diagnostic_test_id: int | None = None,
        confidence: float = 0.6,
    ) -> TopicScore:
        now = datetime.now(timezone.utc)
        existing = (
            await self.session.execute(
                select(TopicScore).where(
                    TopicScore.tenant_id == tenant_id,
                    TopicScore.user_id == user_id,
                    TopicScore.topic_id == topic_id,
                )
            )
        ).scalar_one_or_none()

        previous_interval_days = int(getattr(existing, "revision_interval_days", getattr(existing, "review_interval_days", 1)) or 1) if existing is not None else 1
        last_seen = getattr(existing, "last_seen", None) if existing is not None else None
        days_since_review = max(0, (now.date() - last_seen.date()).days) if last_seen is not None else 0
        schedule = self.schedule_plan(
            score=score,
            confidence=confidence,
            days_since_review=days_since_review,
            previous_interval_days=previous_interval_days,
            performed_well=score >= 75.0,
        )
        interval = int(schedule["review_interval_days"])
        due_at = schedule["review_due_at"]
        if existing is None:
            row = TopicScore(
                tenant_id=tenant_id,
                user_id=user_id,
                topic_id=topic_id,
                diagnostic_test_id=diagnostic_test_id,
                score=score,
                mastery_delta=score,
                confidence=confidence,
                retention_score=float(schedule["retention_score"]),
                review_interval_days=interval,
                revision_interval_days=interval,
                review_due_at=due_at,
                last_seen=now,
                updated_at=now,
            )
            self.session.add(row)
            await self.session.flush()
            return row

        previous_score = float(existing.score)
        existing.diagnostic_test_id = diagnostic_test_id
        existing.score = score
        existing.mastery_delta = round(score - previous_score, 2)
        existing.confidence = confidence
        existing.retention_score = float(schedule["retention_score"])
        existing.review_interval_days = interval
        existing.revision_interval_days = int(schedule["revision_interval_days"])
        existing.review_due_at = due_at
        existing.last_seen = now
        existing.updated_at = now
        await self.session.flush()
        return existing

    async def schedule_topic_review(
        self,
        *,
        tenant_id: int,
        user_id: int,
        topic_id: int,
        completion_score: float,
    ) -> TopicScore | None:
        row = (
            await self.session.execute(
                select(TopicScore).where(
                    TopicScore.tenant_id == tenant_id,
                    TopicScore.user_id == user_id,
                    TopicScore.topic_id == topic_id,
                )
            )
        ).scalar_one_or_none()

        if row is None:
            return await self.upsert_topic_score(
                tenant_id=tenant_id,
                user_id=user_id,
                topic_id=topic_id,
                score=completion_score,
                confidence=0.7,
            )

        row.score = max(float(row.score), completion_score)
        now = datetime.now(timezone.utc)
        previous_interval_days = int(getattr(row, "revision_interval_days", row.review_interval_days) or 1)
        schedule = self.schedule_plan(
            score=float(row.score),
            mastery_delta=float(row.mastery_delta),
            confidence=float(row.confidence),
            days_since_review=0,
            previous_interval_days=previous_interval_days,
            performed_well=completion_score >= 80.0,
        )
        row.retention_score = float(schedule["retention_score"])
        row.review_interval_days = max(int(row.review_interval_days), int(schedule["review_interval_days"]))
        row.revision_interval_days = max(int(getattr(row, "revision_interval_days", row.review_interval_days)), int(schedule["revision_interval_days"]))
        row.review_due_at = now + timedelta(days=int(row.revision_interval_days))
        row.last_seen = now
        row.updated_at = now
        await self.session.flush()
        return row

    async def revisions_due_today(self, *, tenant_id: int, user_id: int) -> dict:
        result = await self.session.execute(
            select(TopicScore, Topic.name)
            .join(Topic, Topic.id == TopicScore.topic_id)
            .where(TopicScore.tenant_id == tenant_id, TopicScore.user_id == user_id)
            .order_by(TopicScore.review_due_at.asc().nulls_last(), TopicScore.retention_score.asc())
        )
        now = datetime.now(timezone.utc)
        revisions = []
        for row, topic_name in result.all():
            due_at = row.review_due_at
            is_due = due_at is not None and due_at <= now
            if not is_due:
                continue
            revisions.append(
                {
                    "topic_id": int(row.topic_id),
                    "topic_name": topic_name,
                    "score": round(float(row.score), 2),
                    "retention_score": round(float(row.retention_score) * 100, 1),
                    "revision_interval_days": int(getattr(row, "revision_interval_days", row.review_interval_days)),
                    "review_due_at": due_at.isoformat() if due_at else None,
                    "last_seen": row.last_seen.isoformat() if getattr(row, "last_seen", None) else None,
                    "is_due": True,
                }
            )

        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "generated_at": now.isoformat(),
            "due_count": len(revisions),
            "revisions": revisions[:10],
        }

    async def learner_retention_summary(self, *, tenant_id: int, user_id: int) -> dict:
        result = await self.session.execute(
            select(TopicScore, Topic.name)
            .join(Topic, Topic.id == TopicScore.topic_id)
            .where(TopicScore.tenant_id == tenant_id, TopicScore.user_id == user_id)
            .order_by(TopicScore.review_due_at.asc().nulls_last(), TopicScore.score.asc())
        )
        rows = result.all()
        now = datetime.now(timezone.utc)

        due_reviews = []
        for row, topic_name in rows:
            due_at = row.review_due_at
            is_due = due_at is not None and due_at <= now
            due_reviews.append(
                {
                    "topic_id": int(row.topic_id),
                    "topic_name": topic_name,
                    "score": round(float(row.score), 2),
                    "retention_score": round(float(row.retention_score) * 100, 1),
                    "review_interval_days": int(getattr(row, "revision_interval_days", row.review_interval_days)),
                    "review_due_at": due_at.isoformat() if due_at else None,
                    "last_seen": row.last_seen.isoformat() if getattr(row, "last_seen", None) else None,
                    "is_due": is_due,
                }
            )

        resources_result = await self.session.execute(
            select(Resource, Topic.name)
            .join(Topic, Topic.id == Resource.topic_id)
            .where(
                Resource.tenant_id == tenant_id,
                Resource.topic_id.in_([item["topic_id"] for item in due_reviews[:3]]) if due_reviews else False,
            )
            .order_by(Resource.rating.desc(), Resource.goal_relevance.desc())
        )
        resource_rows = resources_result.all()
        resource_recommendations = []
        seen_resource_ids: set[int] = set()
        for resource, topic_name in resource_rows:
            if resource.id in seen_resource_ids:
                continue
            seen_resource_ids.add(resource.id)
            resource_recommendations.append(
                {
                    "id": int(resource.id),
                    "topic_id": int(resource.topic_id),
                    "topic_name": topic_name,
                    "title": resource.title,
                    "resource_type": resource.resource_type,
                    "difficulty": resource.difficulty,
                    "rating": round(float(resource.rating), 2),
                    "url": resource.url,
                }
            )
            if len(resource_recommendations) >= 4:
                break

        avg_retention = round(
            sum(float(item["retention_score"]) for item in due_reviews) / max(len(due_reviews), 1),
            1,
        ) if due_reviews else 0.0

        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "average_retention_score": avg_retention,
            "due_reviews": [item for item in due_reviews if item["is_due"]][:6],
            "upcoming_reviews": [item for item in due_reviews if not item["is_due"]][:6],
            "recommended_resources": resource_recommendations,
        }

    async def tenant_retention_summary(self, *, tenant_id: int) -> dict:
        scores_result = await self.session.execute(
            select(TopicScore, Topic.name)
            .join(Topic, Topic.id == TopicScore.topic_id)
            .where(TopicScore.tenant_id == tenant_id)
        )
        rows = scores_result.all()
        now = datetime.now(timezone.utc)
        topic_buckets: dict[str, list[float]] = defaultdict(list)
        due_count = 0
        for row, topic_name in rows:
            topic_buckets[topic_name].append(float(row.retention_score) * 100)
            if row.review_due_at is not None and row.review_due_at <= now:
                due_count += 1

        curve = []
        for offset in range(6, -1, -1):
            day = (now - timedelta(days=offset)).date()
            day_events_result = await self.session.execute(
                select(func.count(LearningEvent.id))
                .where(
                    LearningEvent.tenant_id == tenant_id,
                    LearningEvent.event_type.in_(["topic_completed", "study_session", "practice_quiz"]),
                    func.date(LearningEvent.created_at) == day,
                )
            )
            engagement = int(day_events_result.scalar_one() or 0)
            avg_retention = round(
                sum(sum(values) / len(values) for values in topic_buckets.values()) / max(len(topic_buckets), 1),
                1,
            ) if topic_buckets else 0.0
            curve.append(
                {
                    "label": day.strftime("%a"),
                    "engagement_events": engagement,
                    "average_retention_score": avg_retention,
                }
            )

        weak_topics = [
            {
                "topic_name": topic_name,
                "average_retention_score": round(sum(values) / len(values), 1),
                "learner_count": len(values),
            }
            for topic_name, values in topic_buckets.items()
        ]
        weak_topics.sort(key=lambda item: item["average_retention_score"])

        return {
            "tenant_id": tenant_id,
            "due_review_count": due_count,
            "retention_curve": curve,
            "weak_retention_topics": weak_topics[:8],
        }
