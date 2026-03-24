from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.learning_intelligence_service import LearningIntelligenceService
from app.application.services.mentor_memory_service import MentorMemoryService
from app.application.services.mentor_notification_service import MentorNotificationService
from app.application.services.roadmap_service import RoadmapService
from app.domain.models.mentor_suggestion import MentorSuggestion
from app.domain.models.roadmap import Roadmap
from app.domain.models.topic import Topic


class AutonomousLearningAgentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.learning_intelligence_service = LearningIntelligenceService(session)
        self.mentor_memory_service = MentorMemoryService(session)
        self.roadmap_service = RoadmapService(session)
        self.notification_service = MentorNotificationService()

    async def _topic_names(self, tenant_id: int) -> dict[int, str]:
        result = await self.session.execute(select(Topic.id, Topic.name).where(Topic.tenant_id == tenant_id))
        return {int(topic_id): str(topic_name) for topic_id, topic_name in result.all()}

    async def _latest_roadmap(self, user_id: int, tenant_id: int) -> Roadmap | None:
        return await self.roadmap_service.roadmap_repository.get_latest_roadmap_for_user(
            user_id=user_id,
            tenant_id=tenant_id,
        )

    async def observe(self, *, user_id: int, tenant_id: int) -> dict:
        dashboard = await self.learning_intelligence_service.student_dashboard(user_id=user_id, tenant_id=tenant_id)
        memory = await self.mentor_memory_service.get_snapshot(tenant_id=tenant_id, user_id=user_id)
        roadmap = await self._latest_roadmap(user_id=user_id, tenant_id=tenant_id)
        topic_names = await self._topic_names(tenant_id)

        steps = sorted(roadmap.steps, key=lambda item: item.priority) if roadmap else []
        pending_steps = [step for step in steps if str(step.progress_status).lower() == "pending"]
        in_progress_steps = [step for step in steps if str(step.progress_status).lower() == "in_progress"]
        completed_steps = [step for step in steps if str(step.progress_status).lower() == "completed"]
        next_pending = pending_steps[0] if pending_steps else None
        weakest = (dashboard.get("weak_topics") or [])[:3]
        due_reviews = dashboard.get("retention", {}).get("due_reviews", []) or []
        last_activity = (dashboard.get("recent_activity") or [None])[0]

        notifications = self.notification_service.build_notifications(
            roadmap_steps=[
                {
                    "topic_id": int(step.topic_id),
                    "progress_status": str(step.progress_status),
                    "deadline": step.deadline,
                }
                for step in steps
            ],
            topic_scores={
                int(item["topic_id"]): float(item["score"])
                for item in dashboard.get("weak_topic_heatmap", [])
            },
            last_activity_at=None,
        )

        risk_level = "low"
        if dashboard.get("focus_score", 0) < 45 or len(weakest) >= 3:
            risk_level = "high"
        elif dashboard.get("focus_score", 0) < 65 or due_reviews:
            risk_level = "medium"

        return {
            "roadmap_id": int(roadmap.id) if roadmap else None,
            "completion_percent": float(dashboard.get("completion_percent", 0.0)),
            "focus_score": float(dashboard.get("focus_score", 0.0)),
            "streak_days": int(dashboard.get("streak_days", 0)),
            "xp": int(dashboard.get("xp", 0)),
            "risk_level": risk_level,
            "weak_topics": [
                {
                    "topic_id": int(item["topic_id"]),
                    "topic_name": topic_names.get(int(item["topic_id"]), f"Topic {item['topic_id']}"),
                    "score": float(item["score"]),
                }
                for item in weakest
            ],
            "due_reviews": due_reviews[:3],
            "next_pending_topic": (
                {
                    "topic_id": int(next_pending.topic_id),
                    "topic_name": topic_names.get(int(next_pending.topic_id), f"Topic {next_pending.topic_id}"),
                    "priority": int(next_pending.priority),
                }
                if next_pending is not None
                else None
            ),
            "active_topic_count": len(in_progress_steps),
            "completed_topic_count": len(completed_steps),
            "last_activity": last_activity,
            "memory_summary": {
                "learner_summary": memory.learner_summary,
                "weak_topics": memory.weak_topics[:4],
                "strong_topics": memory.strong_topics[:4],
                "preferred_learning_style": memory.preferred_learning_style,
                "learning_speed": memory.learning_speed,
                "recent_session_summaries": memory.recent_session_summaries[:2],
            },
            "notification_candidates": [
                {
                    "trigger": item.trigger,
                    "severity": item.severity,
                    "title": item.title,
                    "message": item.message,
                }
                for item in notifications[:3]
            ],
        }

    def decide(self, observation: dict) -> list[dict]:
        decisions: list[dict] = []
        next_pending = observation.get("next_pending_topic")
        weak_topics = observation.get("weak_topics", [])
        due_reviews = observation.get("due_reviews", [])
        active_topic_count = int(observation.get("active_topic_count", 0))
        streak_days = int(observation.get("streak_days", 0))
        focus_score = float(observation.get("focus_score", 0.0))

        if next_pending and active_topic_count == 0:
            decisions.append(
                {
                    "decision_type": "next_topic",
                    "priority": "high",
                    "confidence": 0.86,
                    "topic_id": int(next_pending["topic_id"]),
                    "title": f"Start {next_pending['topic_name']} next",
                    "why": "There is no active roadmap step, so the agent selects the highest-priority pending topic to restore momentum.",
                }
            )

        if due_reviews:
            first_review = due_reviews[0]
            decisions.append(
                {
                    "decision_type": "revision",
                    "priority": "high",
                    "confidence": 0.83,
                    "topic_id": int(first_review.get("topic_id", 0) or 0) or None,
                    "title": f"Revise {first_review.get('topic_name', 'a weak topic')}",
                    "why": "Retention signals show a review is due, so the agent prioritizes reinforcement before new material compounds the gap.",
                }
            )

        if weak_topics:
            weakest = weak_topics[0]
            decisions.append(
                {
                    "decision_type": "test",
                    "priority": "medium",
                    "confidence": 0.78,
                    "topic_id": int(weakest["topic_id"]),
                    "title": f"Test understanding on {weakest['topic_name']}",
                    "why": "The learner still has a weak-topic signal here, so a short diagnostic check can confirm whether the gap is conceptual or retention-based.",
                }
            )

        if focus_score < 55 or streak_days == 0:
            decisions.append(
                {
                    "decision_type": "motivation",
                    "priority": "medium",
                    "confidence": 0.74,
                    "topic_id": int(next_pending["topic_id"]) if next_pending else None,
                    "title": "Trigger a low-friction study nudge",
                    "why": "Momentum is weak, so the agent should recommend a small action instead of a heavy plan.",
                }
            )

        if not decisions and next_pending:
            decisions.append(
                {
                    "decision_type": "continue",
                    "priority": "low",
                    "confidence": 0.7,
                    "topic_id": int(next_pending["topic_id"]),
                    "title": f"Continue with {next_pending['topic_name']}",
                    "why": "The learner is on track, so the best action is to continue the current roadmap without intervention.",
                }
            )

        return decisions

    async def _store_suggestion(
        self,
        *,
        tenant_id: int,
        user_id: int,
        topic_id: int | None,
        suggestion_type: str,
        title: str,
        message: str,
        why_reason: str,
    ) -> None:
        self.session.add(
            MentorSuggestion(
                tenant_id=tenant_id,
                user_id=user_id,
                topic_id=topic_id,
                suggestion_type=suggestion_type,
                title=title[:255],
                message=message[:2000],
                why_reason=why_reason[:2000],
                is_ai_generated=True,
                created_at=datetime.now(timezone.utc),
            )
        )

    async def run_cycle(self, *, user_id: int, tenant_id: int, execute_actions: bool = True) -> dict:
        observation = await self.observe(user_id=user_id, tenant_id=tenant_id)
        decisions = self.decide(observation)
        actions: list[dict] = []

        if execute_actions:
            should_refresh_roadmap = any(item["decision_type"] in {"revision", "next_topic"} for item in decisions)
            if should_refresh_roadmap and observation.get("roadmap_id") is not None:
                refresh_result = await self.roadmap_service.adapt_latest(user_id=user_id, tenant_id=tenant_id)
                actions.append(
                    {
                        "action_type": "update_roadmap",
                        "status": "completed",
                        "title": "Roadmap reprioritized",
                        "details": refresh_result,
                        "why": "The agent detected either a missing active topic or a revision need and refreshed the roadmap accordingly.",
                    }
                )

            for decision in decisions[:3]:
                topic_id = decision.get("topic_id")
                await self._store_suggestion(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    topic_id=int(topic_id) if isinstance(topic_id, int) else None,
                    suggestion_type=str(decision["decision_type"]),
                    title=str(decision["title"]),
                    message=str(decision["title"]),
                    why_reason=str(decision["why"]),
                )
                actions.append(
                    {
                        "action_type": "suggest_content",
                        "status": "completed",
                        "title": decision["title"],
                        "details": {"topic_id": topic_id, "priority": decision["priority"]},
                        "why": decision["why"],
                    }
                )

            for notification in observation.get("notification_candidates", [])[:2]:
                actions.append(
                    {
                        "action_type": "send_notification",
                        "status": "prepared",
                        "title": notification["title"],
                        "details": notification,
                        "why": "The agent surfaced this notification from deadline, inactivity, or weakness signals.",
                    }
                )

            await self.session.commit()

        next_best_topic_id = next(
            (int(item["topic_id"]) for item in decisions if item.get("topic_id")),
            None,
        )

        return {
            "agent_mode": "autonomous_guidance",
            "observed_state": observation,
            "decisions": decisions,
            "actions": actions,
            "notifications": observation.get("notification_candidates", []),
            "memory_summary": observation.get("memory_summary", {}),
            "next_best_topic_id": next_best_topic_id,
            "cycle_summary": (
                "The agent observed learner momentum, weak topics, roadmap state, and long-term memory, "
                "then selected the next intervention with explicit rationale."
            ),
        }
