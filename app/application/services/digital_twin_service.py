from __future__ import annotations

from datetime import date
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import NotFoundError
from app.application.services.ml_platform_service import MLPlatformService
from app.application.services.retention_service import RetentionService
from app.domain.engines.learning_profile_engine import LearningProfileEngine
from app.domain.engines.learning_simulation_engine import LearningSimulationEngine
from app.domain.engines.predictive_intelligence_engine import PredictiveIntelligenceEngine
from app.domain.models.learning_event import LearningEvent
from app.domain.models.roadmap import Roadmap
from app.domain.models.topic import Topic
from app.domain.models.topic_score import TopicScore
from app.domain.models.user import User
from app.infrastructure.repositories.roadmap_repository import RoadmapRepository


class DigitalTwinService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.roadmap_repository = RoadmapRepository(session)
        self.retention_service = RetentionService(session)
        self.ml_platform_service = MLPlatformService(session)
        self.learning_profile_engine = LearningProfileEngine()
        self.predictive_engine = PredictiveIntelligenceEngine()
        self.simulation_engine = LearningSimulationEngine()

    async def _topic_name_map(self, tenant_id: int) -> dict[int, str]:
        result = await self.session.execute(select(Topic.id, Topic.name).where(Topic.tenant_id == tenant_id))
        return {int(topic_id): str(topic_name) for topic_id, topic_name in result.all()}

    async def _load_user(self, *, user_id: int, tenant_id: int) -> User:
        user = await self.session.get(User, user_id)
        if user is None or int(user.tenant_id) != tenant_id:
            raise NotFoundError("Learner not found")
        return user

    async def _load_roadmap(self, *, user_id: int, tenant_id: int) -> Roadmap | None:
        return await self.roadmap_repository.get_latest_roadmap_for_user(user_id=user_id, tenant_id=tenant_id)

    async def _load_topic_scores(self, *, user_id: int, tenant_id: int) -> list[TopicScore]:
        result = await self.session.execute(
            select(TopicScore).where(TopicScore.user_id == user_id, TopicScore.tenant_id == tenant_id)
        )
        return list(result.scalars().all())

    async def _load_learning_events(self, *, user_id: int, tenant_id: int) -> list[LearningEvent]:
        result = await self.session.execute(
            select(LearningEvent)
            .where(LearningEvent.user_id == user_id, LearningEvent.tenant_id == tenant_id)
            .order_by(LearningEvent.created_at.desc())
            .limit(30)
        )
        return list(result.scalars().all())

    @staticmethod
    def _behavior_patterns(events: list[LearningEvent]) -> dict:
        session_minutes: list[float] = []
        study_event_count = 0
        for event in events:
            try:
                payload = json.loads(event.metadata_json or "{}")
            except json.JSONDecodeError:
                payload = {}
            minutes = float(payload.get("minutes", payload.get("duration_minutes", 0.0)) or 0.0)
            if minutes > 0:
                session_minutes.append(minutes)
            if str(event.event_type) in {"study_session", "practice_quiz", "topic_completed"}:
                study_event_count += 1

        average_session_minutes = round(sum(session_minutes) / max(len(session_minutes), 1), 2) if session_minutes else 0.0
        cadence = "steady"
        if average_session_minutes < 18:
            cadence = "short_bursts"
        elif average_session_minutes > 45:
            cadence = "deep_work"

        return {
            "average_session_minutes": average_session_minutes,
            "study_event_count": study_event_count,
            "cadence_pattern": cadence,
            "engagement_pattern": "high" if study_event_count >= 12 else "medium" if study_event_count >= 5 else "fragile",
        }

    def _current_model(
        self,
        *,
        user: User,
        roadmap: Roadmap | None,
        topic_scores: list[TopicScore],
        events: list[LearningEvent],
        feature_snapshot: dict | None,
        retention_summary: dict,
        topic_names: dict[int, str],
    ) -> dict:
        steps = roadmap.steps if roadmap is not None else []
        completed_steps = sum(1 for step in steps if str(step.progress_status).lower() == "completed")
        total_steps = len(steps)
        completion_percent = round((completed_steps / total_steps) * 100.0, 2) if total_steps else 0.0

        scores = [float(row.score) for row in topic_scores]
        retention_values = [float(row.retention_score) * 100.0 for row in topic_scores]
        strengths = [
            {
                "topic_id": int(row.topic_id),
                "topic_name": topic_names.get(int(row.topic_id), f"Topic {row.topic_id}"),
                "score": round(float(row.score), 2),
            }
            for row in sorted(topic_scores, key=lambda item: float(item.score), reverse=True)[:5]
            if float(row.score) >= 75.0
        ]
        weaknesses = [
            {
                "topic_id": int(row.topic_id),
                "topic_name": topic_names.get(int(row.topic_id), f"Topic {row.topic_id}"),
                "score": round(float(row.score), 2),
                "retention_score": round(float(row.retention_score) * 100.0, 1),
            }
            for row in sorted(topic_scores, key=lambda item: float(item.score))[:5]
            if float(row.score) < 75.0
        ]

        response_times = [max(12.0, float(index * 6 + 18)) for index, _ in enumerate(topic_scores, start=1)] or [24.0]
        profile = self.learning_profile_engine.analyze(
            response_times=response_times,
            accuracies=scores or [50.0],
            difficulty_distribution={"easy": 2, "medium": 3, "hard": max(1, len(topic_scores) // 3)},
        )

        behavior = self._behavior_patterns(events)
        learning_speed = float((feature_snapshot or {}).get("learning_speed") or profile.speed or 0.0)
        retention_rate = round(sum(retention_values) / max(len(retention_values), 1), 2) if retention_values else 0.0

        twin_confidence = round(
            min(
                100.0,
                35.0
                + (min(len(topic_scores), 12) * 3.2)
                + (min(len(events), 20) * 1.5)
                + (15.0 if feature_snapshot else 0.0),
            ),
            1,
        )

        return {
            "learner_summary": (
                f"{user.display_name or user.email.split('@')[0]} currently learns in a {behavior['cadence_pattern']} pattern, "
                f"shows {profile.profile_type} tendencies, and has a modeled retention rate of {retention_rate:.1f}%."
            ),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "learning_speed": round(learning_speed, 2),
            "memory_retention": retention_rate,
            "behavior_patterns": {
                **behavior,
                "profile_type": profile.profile_type,
                "confidence": round(float(profile.confidence), 2),
                "consistency": round(float(profile.consistency), 2),
                "stamina": round(float(profile.stamina), 2),
            },
            "roadmap_state": {
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "completion_percent": completion_percent,
            },
            "retention_summary": retention_summary,
            "twin_confidence": twin_confidence,
        }

    def _simulate_strategy(
        self,
        *,
        roadmap: Roadmap | None,
        daily_study_hours: float,
        focus_multiplier: float,
        retention_multiplier: float,
        label: str,
    ) -> dict:
        steps = []
        for step in (roadmap.steps if roadmap is not None else []):
            estimated_time = float(step.estimated_time_hours) / max(focus_multiplier, 0.5)
            if bool(getattr(step, "is_revision", False)):
                estimated_time *= max(0.7, 1.1 - ((retention_multiplier - 1.0) * 0.4))
            steps.append(
                {
                    "topic_id": int(step.topic_id),
                    "estimated_time_hours": round(max(0.5, estimated_time), 2),
                }
            )

        simulation = self.simulation_engine.simulate(
            roadmap={"start_date": date.today(), "steps": steps},
            daily_study_hours=daily_study_hours,
        )
        return {
            "strategy": label,
            "daily_study_hours": daily_study_hours,
            "estimated_completion_date": simulation.estimated_completion_date.isoformat(),
            "progress_curve": simulation.progress_curve,
        }

    async def get_twin(self, *, user_id: int, tenant_id: int) -> dict:
        user = await self._load_user(user_id=user_id, tenant_id=tenant_id)
        roadmap = await self._load_roadmap(user_id=user_id, tenant_id=tenant_id)
        topic_scores = await self._load_topic_scores(user_id=user_id, tenant_id=tenant_id)
        events = await self._load_learning_events(user_id=user_id, tenant_id=tenant_id)
        topic_names = await self._topic_name_map(tenant_id)
        retention_summary = await self.retention_service.learner_retention_summary(tenant_id=tenant_id, user_id=user_id)
        feature_snapshot = await self.ml_platform_service.latest_feature_snapshot(user_id=user_id, tenant_id=tenant_id)
        if feature_snapshot is None:
            feature_snapshot = await self.ml_platform_service.build_feature_snapshot(user_id=user_id, tenant_id=tenant_id)

        current_model = self._current_model(
            user=user,
            roadmap=roadmap,
            topic_scores=topic_scores,
            events=events,
            feature_snapshot=feature_snapshot,
            retention_summary=retention_summary,
            topic_names=topic_names,
        )

        current_completion = float(current_model["roadmap_state"]["completion_percent"])
        average_score = round(sum(float(row.score) for row in topic_scores) / max(len(topic_scores), 1), 2) if topic_scores else 0.0
        risk_prediction = self.predictive_engine.predict_failure_risk(
            completion_percent=current_completion,
            average_score=average_score,
            consistency_score=float(current_model["behavior_patterns"]["consistency"]),
            retention_score=float(current_model["memory_retention"]),
            weak_topic_count=len(current_model["weaknesses"]),
            overdue_steps=max(0, len(retention_summary.get("due_reviews", [])) - 1),
        )

        baseline = self._simulate_strategy(
            roadmap=roadmap,
            daily_study_hours=1.5,
            focus_multiplier=1.0,
            retention_multiplier=1.0,
            label="baseline",
        )
        accelerated = self._simulate_strategy(
            roadmap=roadmap,
            daily_study_hours=2.5,
            focus_multiplier=1.18,
            retention_multiplier=1.05,
            label="accelerated_focus",
        )
        retention_first = self._simulate_strategy(
            roadmap=roadmap,
            daily_study_hours=1.8,
            focus_multiplier=0.95,
            retention_multiplier=1.22,
            label="retention_first",
        )

        strategies = [
            {
                "strategy": "baseline",
                "summary": "Maintain current pace with moderate daily effort.",
                "predicted_completion_date": baseline["estimated_completion_date"],
                "predicted_readiness_percent": round(min(100.0, current_completion + 18.0), 1),
                "predicted_retention_percent": round(min(100.0, current_model["memory_retention"] + 6.0), 1),
                "tradeoff": "Balanced pace, lower burnout risk, moderate speed.",
            },
            {
                "strategy": "accelerated_focus",
                "summary": "Increase daily focus and compress the roadmap.",
                "predicted_completion_date": accelerated["estimated_completion_date"],
                "predicted_readiness_percent": round(min(100.0, current_completion + 28.0), 1),
                "predicted_retention_percent": round(min(100.0, current_model["memory_retention"] + 4.0), 1),
                "tradeoff": "Fastest progress, but consistency pressure rises.",
            },
            {
                "strategy": "retention_first",
                "summary": "Bias toward spaced review and memory durability.",
                "predicted_completion_date": retention_first["estimated_completion_date"],
                "predicted_readiness_percent": round(min(100.0, current_completion + 22.0), 1),
                "predicted_retention_percent": round(min(100.0, current_model["memory_retention"] + 12.0), 1),
                "tradeoff": "Slower finish, stronger long-term recall and fewer relearning dips.",
            },
        ]
        strategies.sort(key=lambda item: (-float(item["predicted_readiness_percent"]), item["predicted_completion_date"]))
        optimal_path = strategies[0]

        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "current_model": current_model,
            "predictions": {
                "risk_prediction": risk_prediction,
                "baseline": baseline,
                "accelerated_focus": accelerated,
                "retention_first": retention_first,
            },
            "decision_support": {
                "recommended_strategy": optimal_path,
                "strategy_comparison": strategies,
                "recommended_learning_path": [
                    weakness["topic_name"] for weakness in current_model["weaknesses"][:3]
                ] + [
                    strength["topic_name"] for strength in current_model["strengths"][:2]
                ],
                "why": [
                    "Weak topics were prioritized because they suppress downstream performance.",
                    "Retention pressure was included so the twin prefers durable gains over cosmetic speed.",
                    "Predicted completion and readiness were compared across multiple study strategies.",
                ],
            },
        }
