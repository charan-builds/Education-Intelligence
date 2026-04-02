from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.learning_event import LearningEvent
from app.domain.models.question import Question
from app.domain.models.topic import Topic
from app.domain.models.topic_feature import TopicFeature
from app.domain.models.topic_score import TopicScore
from app.domain.models.user_feature import UserFeature


class FeatureStoreService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_user_features(
        self,
        *,
        tenant_id: int,
        user_id: int,
        feature_set_name: str,
        values: dict,
        updated_at: datetime | None = None,
    ) -> UserFeature:
        timestamp = updated_at or datetime.now(timezone.utc)
        row = await self.session.scalar(
            select(UserFeature).where(
                UserFeature.tenant_id == tenant_id,
                UserFeature.user_id == user_id,
                UserFeature.feature_set_name == feature_set_name,
            )
        )
        if row is None:
            row = UserFeature(
                tenant_id=tenant_id,
                user_id=user_id,
                feature_set_name=feature_set_name,
                feature_values_json=json.dumps(values, ensure_ascii=True, default=str),
                updated_at=timestamp,
            )
            self.session.add(row)
        else:
            row.feature_values_json = json.dumps(values, ensure_ascii=True, default=str)
            row.updated_at = timestamp
        await self.session.flush()
        return row

    async def refresh_topic_features(self, *, tenant_id: int) -> int:
        now = datetime.now(timezone.utc)
        rows = (
            await self.session.execute(
                select(
                    Topic.id,
                    Topic.name,
                    func.avg(Question.difficulty).label("avg_difficulty"),
                    func.avg(TopicScore.score).label("avg_mastery"),
                    func.count(TopicScore.id).label("observations"),
                )
                .select_from(Topic)
                .outerjoin(Question, Question.topic_id == Topic.id)
                .outerjoin(
                    TopicScore,
                    (TopicScore.topic_id == Topic.id) & (TopicScore.tenant_id == Topic.tenant_id),
                )
                .where(Topic.tenant_id == tenant_id)
                .group_by(Topic.id, Topic.name)
            )
        ).all()
        updated = 0
        for topic_id, topic_name, avg_difficulty, avg_mastery, observations in rows:
            payload = {
                "topic_id": int(topic_id),
                "topic_name": str(topic_name),
                "difficulty": round(float(avg_difficulty or 0.0), 2),
                "avg_mastery": round(float(avg_mastery or 0.0), 2),
                "observation_count": int(observations or 0),
            }
            row = await self.session.scalar(
                select(TopicFeature).where(
                    TopicFeature.tenant_id == tenant_id,
                    TopicFeature.topic_id == int(topic_id),
                    TopicFeature.feature_set_name == "topic_features",
                )
            )
            if row is None:
                row = TopicFeature(
                    tenant_id=tenant_id,
                    topic_id=int(topic_id),
                    feature_set_name="topic_features",
                    feature_values_json=json.dumps(payload, ensure_ascii=True),
                    updated_at=now,
                )
                self.session.add(row)
            else:
                row.feature_values_json = json.dumps(payload, ensure_ascii=True)
                row.updated_at = now
            updated += 1
        await self.session.flush()
        return updated

    async def export_training_dataset(self, *, tenant_id: int, user_id: int | None = None) -> list[dict]:
        stmt = (
            select(UserFeature.user_id, UserFeature.feature_values_json)
            .where(UserFeature.tenant_id == tenant_id, UserFeature.feature_set_name == "learner_features")
            .order_by(UserFeature.user_id.asc())
        )
        if user_id is not None:
            stmt = stmt.where(UserFeature.user_id == user_id)
        rows = (await self.session.execute(stmt)).all()
        dataset: list[dict] = []
        for feature_user_id, feature_values_json in rows:
            feature_values = json.loads(feature_values_json or "{}")
            label = await self.session.scalar(
                select(func.count(LearningEvent.id)).where(
                    LearningEvent.tenant_id == tenant_id,
                    LearningEvent.user_id == int(feature_user_id),
                    LearningEvent.event_type == "topic_completed",
                )
            )
            dataset.append(
                {
                    "tenant_id": tenant_id,
                    "user_id": int(feature_user_id),
                    "features": feature_values,
                    "labels": {"topic_completion_events": int(label or 0)},
                }
            )
        return dataset

    async def clear_user_features(self, *, tenant_id: int, user_id: int) -> None:
        await self.session.execute(
            delete(UserFeature).where(UserFeature.tenant_id == tenant_id, UserFeature.user_id == user_id)
        )
