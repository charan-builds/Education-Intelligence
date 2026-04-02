from __future__ import annotations

import json
from statistics import mean

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.mentor_memory_service import MentorMemoryService
from app.domain.models.learning_event import LearningEvent
from app.domain.models.topic import Topic
from app.domain.models.user import User


class AIContextBuilder:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.memory_service = MentorMemoryService(session)

    @staticmethod
    def _learning_speed(recent_activity: list[dict]) -> float:
        durations = [float(item.get("minutes", 0.0)) for item in recent_activity if float(item.get("minutes", 0.0)) > 0]
        return round(mean(durations), 2) if durations else 0.0

    async def build_mentor_context(
        self,
        *,
        user_id: int,
        tenant_id: int,
        learning_profile: dict,
        roadmap_progress: dict,
        weak_topics: list[int],
        topic_scores: dict[int, float],
        cognitive_model: dict | None = None,
    ) -> dict:
        user = await self.session.get(User, user_id)

        topic_name_rows = await self.session.execute(select(Topic.id, Topic.name).where(Topic.tenant_id == tenant_id))
        topic_names = {int(topic_id): str(name) for topic_id, name in topic_name_rows.all()}

        events_result = await self.session.execute(
            select(LearningEvent)
            .where(LearningEvent.tenant_id == tenant_id, LearningEvent.user_id == user_id)
            .order_by(LearningEvent.created_at.desc())
            .limit(6)
        )
        events = events_result.scalars().all()
        recent_activity: list[dict] = []
        for event in events:
            try:
                metadata = json.loads(event.metadata_json or "{}")
            except json.JSONDecodeError:
                metadata = {}
            recent_activity.append(
                {
                    "event_type": event.event_type,
                    "topic_name": topic_names.get(int(event.topic_id), f"Topic {event.topic_id}") if event.topic_id else None,
                    "created_at": event.created_at.isoformat(),
                    "minutes": float(metadata.get("minutes", metadata.get("duration_minutes", 0.0)) or 0.0),
                }
            )

        weak_topic_details = [
            {
                "topic_id": int(topic_id),
                "topic_name": topic_names.get(int(topic_id), f"Topic {topic_id}"),
                "score": round(float(topic_scores.get(topic_id, 0.0)), 2),
            }
            for topic_id in weak_topics[:4]
        ]
        strong_topic_details = [
            {
                "topic_id": int(topic_id),
                "topic_name": topic_names.get(int(topic_id), f"Topic {topic_id}"),
                "score": round(float(score), 2),
            }
            for topic_id, score in sorted(topic_scores.items(), key=lambda item: item[1], reverse=True)[:3]
            if float(score) >= 75.0
        ]

        memory_snapshot = await self.memory_service.get_snapshot(tenant_id=tenant_id, user_id=user_id)

        return {
            "user_profile": {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "display_name": user.display_name if user is not None else None,
                "preferred_learning_style": memory_snapshot.preferred_learning_style or learning_profile.get("profile_type", "balanced"),
                "learning_profile": learning_profile,
                "learning_speed": memory_snapshot.learning_speed or self._learning_speed(recent_activity),
            },
            "roadmap_progress": roadmap_progress,
            "weak_topics": weak_topic_details,
            "strong_topics": strong_topic_details,
            "recent_activity": recent_activity,
            "memory_profile": {
                "learner_summary": memory_snapshot.learner_summary,
                "weak_topics_history": memory_snapshot.weak_topics,
                "strong_topics_history": memory_snapshot.strong_topics,
                "past_mistakes": memory_snapshot.past_mistakes[:3],
                "improvement_signals": memory_snapshot.improvement_signals[:3],
                "last_session_summary": memory_snapshot.last_session_summary,
                "recent_session_summaries": memory_snapshot.recent_session_summaries[:2],
            },
            "cognitive_model": cognitive_model or {},
        }
