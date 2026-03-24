from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.mentor_memory_profile import MentorMemoryProfile
from app.domain.models.mentor_session_memory import MentorSessionMemory


@dataclass(frozen=True)
class LearnerMemorySnapshot:
    learner_summary: str
    weak_topics: list[str]
    strong_topics: list[str]
    past_mistakes: list[str]
    improvement_signals: list[str]
    preferred_learning_style: str
    learning_speed: float
    last_session_summary: str
    recent_session_summaries: list[str]


class MentorMemoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _loads_list(value: str | None) -> list[str]:
        if not value:
            return []
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return []
        if not isinstance(payload, list):
            return []
        return [str(item) for item in payload if str(item).strip()]

    @staticmethod
    def _dumps_list(items: list[str], *, limit: int = 8) -> str:
        unique: list[str] = []
        seen: set[str] = set()
        for item in items:
            normalized = str(item).strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(normalized[:240])
            if len(unique) >= limit:
                break
        return json.dumps(unique, ensure_ascii=True)

    async def get_snapshot(self, *, tenant_id: int, user_id: int) -> LearnerMemorySnapshot:
        profile_result = await self.session.execute(
            select(MentorMemoryProfile)
            .where(MentorMemoryProfile.tenant_id == tenant_id, MentorMemoryProfile.user_id == user_id)
            .limit(1)
        )
        profile = profile_result.scalar_one_or_none()

        session_rows = await self.session.execute(
            select(MentorSessionMemory)
            .where(MentorSessionMemory.tenant_id == tenant_id, MentorSessionMemory.user_id == user_id)
            .order_by(MentorSessionMemory.created_at.desc())
            .limit(3)
        )
        recent_sessions = session_rows.scalars().all()

        if profile is None:
            return LearnerMemorySnapshot(
                learner_summary="No long-term learner memory has been stored yet.",
                weak_topics=[],
                strong_topics=[],
                past_mistakes=[],
                improvement_signals=[],
                preferred_learning_style="balanced",
                learning_speed=0.0,
                last_session_summary="",
                recent_session_summaries=[session.summary for session in recent_sessions],
            )

        return LearnerMemorySnapshot(
            learner_summary=profile.learner_summary,
            weak_topics=self._loads_list(profile.weak_topics_json),
            strong_topics=self._loads_list(profile.strong_topics_json),
            past_mistakes=self._loads_list(profile.past_mistakes_json),
            improvement_signals=self._loads_list(profile.improvement_signals_json),
            preferred_learning_style=profile.preferred_learning_style,
            learning_speed=float(profile.learning_speed or 0.0),
            last_session_summary=profile.last_session_summary,
            recent_session_summaries=[session.summary for session in recent_sessions],
        )

    async def update_after_session(
        self,
        *,
        tenant_id: int,
        user_id: int,
        user_message: str,
        mentor_reply: str,
        memory_update: dict | None = None,
    ) -> LearnerMemorySnapshot:
        memory_update = memory_update or {}
        snapshot = await self.get_snapshot(tenant_id=tenant_id, user_id=user_id)
        now = datetime.now(timezone.utc)

        profile_result = await self.session.execute(
            select(MentorMemoryProfile)
            .where(MentorMemoryProfile.tenant_id == tenant_id, MentorMemoryProfile.user_id == user_id)
            .limit(1)
        )
        profile = profile_result.scalar_one_or_none()
        if profile is None:
            profile = MentorMemoryProfile(
                tenant_id=tenant_id,
                user_id=user_id,
                updated_at=now,
            )
            self.session.add(profile)

        weak_topics = [str(item) for item in memory_update.get("weak_topics", [])] or snapshot.weak_topics
        strong_topics = [str(item) for item in memory_update.get("strong_topics", [])] or snapshot.strong_topics
        past_mistakes = [str(item) for item in memory_update.get("past_mistakes", [])] or snapshot.past_mistakes
        improvement_signals = [str(item) for item in memory_update.get("improvement_signals", [])] or snapshot.improvement_signals
        session_summary = str(memory_update.get("session_summary") or "").strip() or (
            f"Learner asked about '{user_message[:120]}'. Mentor emphasized '{mentor_reply[:160]}'."
        )
        learner_summary = str(memory_update.get("learner_summary") or "").strip() or snapshot.learner_summary
        if learner_summary == "No long-term learner memory has been stored yet.":
            learner_summary = session_summary

        profile.learner_summary = learner_summary[:1500]
        profile.weak_topics_json = self._dumps_list(weak_topics)
        profile.strong_topics_json = self._dumps_list(strong_topics)
        profile.past_mistakes_json = self._dumps_list(past_mistakes)
        profile.improvement_signals_json = self._dumps_list(improvement_signals)
        profile.preferred_learning_style = str(
            memory_update.get("preferred_learning_style") or snapshot.preferred_learning_style or "balanced"
        )[:64]
        profile.learning_speed = float(memory_update.get("learning_speed") or snapshot.learning_speed or 0.0)
        profile.last_session_summary = session_summary[:1500]
        profile.updated_at = now

        session_record = MentorSessionMemory(
            tenant_id=tenant_id,
            user_id=user_id,
            source="mentor_chat",
            summary=session_summary[:1500],
            discussed_topics_json=self._dumps_list([*weak_topics[:3], *strong_topics[:2]], limit=6),
            mistakes_json=self._dumps_list(past_mistakes, limit=6),
            insights_json=self._dumps_list(improvement_signals, limit=6),
            created_at=now,
        )
        self.session.add(session_record)
        await self.session.commit()

        return await self.get_snapshot(tenant_id=tenant_id, user_id=user_id)
