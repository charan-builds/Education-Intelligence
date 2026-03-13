from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class MentorNotification:
    trigger: str
    severity: str
    title: str
    message: str


class MentorNotificationService:
    TRIGGER_ROADMAP_DEADLINE = "roadmap_deadline"
    TRIGGER_LEARNING_INACTIVITY = "learning_inactivity"
    TRIGGER_TOPIC_WEAKNESS = "topic_weakness"

    def build_notifications(
        self,
        *,
        roadmap_steps: list[dict],
        topic_scores: dict[int, float],
        last_activity_at: datetime | None,
        now: datetime | None = None,
        inactivity_days_threshold: int = 3,
        weakness_threshold: float = 70.0,
    ) -> list[MentorNotification]:
        current = now or datetime.now(timezone.utc)
        notifications: list[MentorNotification] = []

        notifications.extend(self._roadmap_deadline_notifications(roadmap_steps=roadmap_steps, now=current))
        inactivity = self._learning_inactivity_notification(
            last_activity_at=last_activity_at,
            now=current,
            threshold_days=inactivity_days_threshold,
        )
        if inactivity is not None:
            notifications.append(inactivity)

        weakness = self._topic_weakness_notification(topic_scores=topic_scores, threshold=weakness_threshold)
        if weakness is not None:
            notifications.append(weakness)

        return notifications

    def _roadmap_deadline_notifications(
        self,
        *,
        roadmap_steps: list[dict],
        now: datetime,
    ) -> list[MentorNotification]:
        items: list[MentorNotification] = []
        for step in roadmap_steps:
            status = str(step.get("progress_status", "pending")).lower()
            if status == "completed":
                continue

            deadline = step.get("deadline")
            if not isinstance(deadline, datetime):
                continue

            topic_id = step.get("topic_id")
            if deadline < now:
                items.append(
                    MentorNotification(
                        trigger=self.TRIGGER_ROADMAP_DEADLINE,
                        severity="high",
                        title="Roadmap deadline missed",
                        message=f"Topic {topic_id} is overdue. Re-plan this step today.",
                    )
                )
            elif deadline <= now + timedelta(days=2):
                items.append(
                    MentorNotification(
                        trigger=self.TRIGGER_ROADMAP_DEADLINE,
                        severity="medium",
                        title="Roadmap deadline approaching",
                        message=f"Topic {topic_id} is due soon. Schedule focused study time.",
                    )
                )
        return items

    def _learning_inactivity_notification(
        self,
        *,
        last_activity_at: datetime | None,
        now: datetime,
        threshold_days: int,
    ) -> MentorNotification | None:
        if last_activity_at is None:
            return MentorNotification(
                trigger=self.TRIGGER_LEARNING_INACTIVITY,
                severity="medium",
                title="No recent learning activity",
                message="Start with one small study session today to rebuild momentum.",
            )

        if last_activity_at.tzinfo is None:
            last_activity_at = last_activity_at.replace(tzinfo=timezone.utc)

        inactive_days = (now - last_activity_at).days
        if inactive_days >= threshold_days:
            return MentorNotification(
                trigger=self.TRIGGER_LEARNING_INACTIVITY,
                severity="medium" if inactive_days < 7 else "high",
                title="Learning inactivity detected",
                message=f"You have been inactive for {inactive_days} days. Resume with a short roadmap step.",
            )
        return None

    def _topic_weakness_notification(
        self,
        *,
        topic_scores: dict[int, float],
        threshold: float,
    ) -> MentorNotification | None:
        weak = sorted(topic_id for topic_id, score in topic_scores.items() if float(score) < threshold)
        if not weak:
            return None

        top_weak = ", ".join(map(str, weak[:5]))
        return MentorNotification(
            trigger=self.TRIGGER_TOPIC_WEAKNESS,
            severity="high" if len(weak) >= 3 else "medium",
            title="Topic weakness detected",
            message=f"Review weak topics: {top_weak}. Focus on prerequisites first.",
        )
