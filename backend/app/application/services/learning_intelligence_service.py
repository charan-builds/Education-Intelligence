from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import NotFoundError
from app.application.services.analytics_service import AnalyticsService
from app.application.services.cognitive_modeling_service import CognitiveModelingService
from app.application.services.retention_service import RetentionService
from app.domain.engines.learning_profile_engine import LearningProfileEngine
from app.domain.engines.predictive_intelligence_engine import PredictiveIntelligenceEngine
from app.domain.engines.weakness_modeling_engine import WeaknessModelingEngine
from app.domain.models.badge import Badge
from app.domain.models.community import Community
from app.domain.models.discussion_reply import DiscussionReply
from app.domain.models.discussion_thread import DiscussionThread
from app.domain.models.experiment import Experiment
from app.domain.models.experiment_variant import ExperimentVariant
from app.domain.models.learning_event import LearningEvent
from app.domain.models.mentor_suggestion import MentorSuggestion
from app.domain.models.roadmap_step import RoadmapStep
from app.domain.models.topic import Topic
from app.domain.models.topic_prerequisite import TopicPrerequisite
from app.domain.models.topic_score import TopicScore
from app.domain.models.user import User, UserRole
from app.domain.models.user_tenant_role import UserTenantRole
from app.infrastructure.repositories.tenant_scoping import user_belongs_to_tenant, user_has_tenant_role
from app.infrastructure.repositories.roadmap_repository import RoadmapRepository


class LearningIntelligenceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.roadmap_repository = RoadmapRepository(session)
        self.analytics_service = AnalyticsService(session)
        self.retention_service = RetentionService(session)
        self.learning_profile_engine = LearningProfileEngine()
        self.cognitive_modeling_service = CognitiveModelingService()
        self.predictive_engine = PredictiveIntelligenceEngine()
        self.weakness_engine = WeaknessModelingEngine()

    @staticmethod
    def _event_minutes(metadata_json: str | None) -> float:
        if not metadata_json:
            return 0.0
        try:
            payload = json.loads(metadata_json)
        except json.JSONDecodeError:
            return 0.0
        return float(payload.get("minutes", payload.get("duration_minutes", 0.0)) or 0.0)

    async def _topic_name_map(self, tenant_id: int) -> dict[int, str]:
        result = await self.session.execute(select(Topic.id, Topic.name).where(Topic.tenant_id == tenant_id))
        return {int(topic_id): name for topic_id, name in result.all()}

    async def _prerequisite_map(self, tenant_id: int) -> dict[int, list[int]]:
        result = await self.session.execute(
            select(TopicPrerequisite.topic_id, TopicPrerequisite.prerequisite_topic_id)
            .join(Topic, Topic.id == TopicPrerequisite.topic_id)
            .where(Topic.tenant_id == tenant_id)
        )
        graph: dict[int, list[int]] = defaultdict(list)
        for topic_id, prerequisite_topic_id in result.all():
            graph[int(topic_id)].append(int(prerequisite_topic_id))
        return dict(graph)

    async def adaptive_refresh(self, *, user_id: int, tenant_id: int) -> dict:
        roadmap = await self.roadmap_repository.get_latest_roadmap_for_user(user_id=user_id, tenant_id=tenant_id)
        if roadmap is None:
            raise NotFoundError("No roadmap found for user")

        topic_scores_result = await self.session.execute(
            select(TopicScore).where(TopicScore.user_id == user_id, TopicScore.tenant_id == tenant_id)
        )
        topic_scores = {row.topic_id: row for row in topic_scores_result.scalars().all()}
        topic_names = await self._topic_name_map(tenant_id)
        prerequisite_map = await self._prerequisite_map(tenant_id)

        completed_ids = {
            int(step.topic_id)
            for step in roadmap.steps
            if str(step.progress_status).lower() == "completed"
        }
        pending_steps = [
            step for step in sorted(roadmap.steps, key=lambda item: item.priority)
            if str(step.progress_status).lower() != "completed"
        ]

        reprioritized: list[dict] = []
        for index, step in enumerate(pending_steps, start=1):
            score_row = topic_scores.get(int(step.topic_id))
            score = float(score_row.score) if score_row is not None else 50.0
            priority_boost = 2 if score < 60 else 1 if score < 75 else 0
            step.priority = index - priority_boost if priority_boost else index
            step.priority = max(1, step.priority)
            if score < 65:
                step.rationale = (
                    f"Re-prioritized because {topic_names.get(step.topic_id, 'this topic')} remains below mastery "
                    f"at {score:.0f}% and needs reinforcement."
                )
            reprioritized.append(
                {
                    "step_id": int(step.id),
                    "topic_id": int(step.topic_id),
                    "topic_name": topic_names.get(int(step.topic_id), f"Topic {step.topic_id}"),
                    "score": round(score, 2),
                    "priority": int(step.priority),
                    "rationale": step.rationale,
                }
            )

        revision_candidates = [
            row for row in topic_scores.values()
            if (float(row.score) < 70 or (float(row.retention_score) * 100) < 65) and int(row.topic_id) in completed_ids
        ]
        revision_candidates.sort(key=lambda item: (float(item.score), -float(item.mastery_delta)))

        inserted_revision = None
        if revision_candidates:
            weakest = revision_candidates[0]
            existing_revision = next(
                (
                    step for step in roadmap.steps
                    if int(step.topic_id) == int(weakest.topic_id)
                    and bool(getattr(step, "is_revision", False))
                    and str(step.progress_status).lower() != "completed"
                ),
                None,
            )
            if existing_revision is None:
                next_priority = max((int(step.priority) for step in roadmap.steps), default=0) + 1
                revision_step = await self.roadmap_repository.add_step(
                    roadmap_id=roadmap.id,
                    topic_id=int(weakest.topic_id),
                    deadline=datetime.now(timezone.utc) + timedelta(days=4),
                    estimated_time_hours=2.0,
                    difficulty="medium",
                    priority=next_priority,
                    progress_status="pending",
                    step_type="revision",
                    rationale=(
                        f"Revision injected because mastery dropped to {float(weakest.score):.0f}% "
                        "after prior completion."
                    ),
                    is_revision=True,
                )
                inserted_revision = {
                    "step_id": int(revision_step.id),
                    "topic_id": int(revision_step.topic_id),
                    "topic_name": topic_names.get(int(revision_step.topic_id), f"Topic {revision_step.topic_id}"),
                    "reason": revision_step.rationale,
                }

        profile = self.learning_profile_engine.analyze(
            response_times=[20.0 + (index * 5.0) for index, _ in enumerate(topic_scores.values(), start=1)] or [25.0],
            accuracies=[float(item.score) for item in topic_scores.values()] or [50.0],
            difficulty_distribution={"easy": 2, "medium": 3, "hard": max(1, len(topic_scores) // 3)},
        )
        weakness_analysis = self.weakness_engine.analyze(
            topic_scores={int(topic_id): float(item.score) for topic_id, item in topic_scores.items()},
            prerequisite_map=prerequisite_map,
            confidence_by_topic={int(topic_id): float(item.confidence) for topic_id, item in topic_scores.items()},
            retention_by_topic={int(topic_id): float(item.retention_score) for topic_id, item in topic_scores.items()},
        )
        overdue_steps = sum(
            1
            for step in roadmap.steps
            if str(step.progress_status).lower() != "completed" and step.deadline <= datetime.now(timezone.utc)
        )
        average_score = (
            sum(float(item.score) for item in topic_scores.values()) / max(len(topic_scores), 1)
            if topic_scores else 0.0
        )
        average_retention = (
            sum(float(item.retention_score) * 100 for item in topic_scores.values()) / max(len(topic_scores), 1)
            if topic_scores else 0.0
        )
        risk_prediction = self.predictive_engine.predict_failure_risk(
            completion_percent=(len(completed_ids) / max(len(roadmap.steps), 1)) * 100.0,
            average_score=average_score,
            consistency_score=profile.consistency,
            retention_score=average_retention,
            weak_topic_count=len(weakness_analysis["deep_weaknesses"]),
            overdue_steps=overdue_steps,
        )

        await self.session.commit()
        return {
            "roadmap_id": roadmap.id,
            "reprioritized_steps": sorted(reprioritized, key=lambda item: item["priority"]),
            "inserted_revision": inserted_revision,
            "risk_prediction": risk_prediction,
            "weakness_clusters": weakness_analysis["weakness_clusters"],
            "learning_profile": {
                "profile_type": profile.profile_type,
                "confidence": profile.confidence,
                "speed": profile.speed,
                "accuracy": profile.accuracy,
                "consistency": profile.consistency,
                "stamina": profile.stamina,
            },
        }

    async def student_dashboard(self, *, user_id: int, tenant_id: int) -> dict:
        user_result = await self.session.execute(
            select(User).where(User.id == user_id, user_belongs_to_tenant(User, tenant_id))
        )
        user = user_result.scalar_one_or_none()
        if user is None:
            raise NotFoundError("Student not found")

        roadmap = await self.roadmap_repository.get_latest_roadmap_for_user(user_id=user_id, tenant_id=tenant_id)
        steps = sorted(roadmap.steps, key=lambda item: item.priority) if roadmap else []
        topic_names = await self._topic_name_map(tenant_id)
        prerequisite_map = await self._prerequisite_map(tenant_id)

        topic_scores_result = await self.session.execute(
            select(TopicScore).where(TopicScore.user_id == user_id, TopicScore.tenant_id == tenant_id)
        )
        topic_scores = topic_scores_result.scalars().all()

        learning_events_result = await self.session.execute(
            select(LearningEvent)
            .where(LearningEvent.user_id == user_id, LearningEvent.tenant_id == tenant_id)
            .order_by(LearningEvent.created_at.desc())
            .limit(64)
        )
        learning_events = learning_events_result.scalars().all()

        suggestions_result = await self.session.execute(
            select(MentorSuggestion)
            .where(MentorSuggestion.user_id == user_id, MentorSuggestion.tenant_id == tenant_id)
            .order_by(MentorSuggestion.created_at.desc())
            .limit(5)
        )
        suggestions = suggestions_result.scalars().all()

        badges_result = await self.session.execute(
            select(Badge).where(Badge.user_id == user_id, Badge.tenant_id == tenant_id).order_by(Badge.awarded_at.desc())
        )
        badges = badges_result.scalars().all()

        total_steps = len(steps)
        completed_steps = sum(1 for step in steps if str(step.progress_status).lower() == "completed")
        in_progress_steps = sum(1 for step in steps if str(step.progress_status).lower() == "in_progress")
        completion_percent = round((completed_steps / total_steps) * 100, 2) if total_steps else 0.0

        today = datetime.now(timezone.utc).date()
        active_days = sorted({event.created_at.date() for event in learning_events}, reverse=True)
        streak = 0
        cursor = today
        for day in active_days:
            if day == cursor:
                streak += 1
                cursor = cursor - timedelta(days=1)
            elif day < cursor:
                break

        events_by_day: dict = defaultdict(list)
        for event in learning_events:
            events_by_day[event.created_at.date()].append(event)

        velocity_points: list[dict] = []
        for offset in range(6, -1, -1):
            day = today - timedelta(days=offset)
            day_events = events_by_day.get(day, [])
            day_minutes = sum(self._event_minutes(event.metadata_json) for event in day_events)
            velocity_points.append(
                {
                    "label": day.strftime("%a"),
                    "minutes": round(day_minutes, 1),
                    "completed_steps": sum(1 for event in day_events if event.event_type == "topic_completed"),
                }
            )

        heatmap = [
            {
                "topic_id": int(score.topic_id),
                "topic_name": topic_names.get(int(score.topic_id), f"Topic {score.topic_id}"),
                "score": round(float(score.score), 2),
                "mastery_delta": round(float(score.mastery_delta), 2),
                "confidence": round(float(score.confidence), 2),
            }
            for score in sorted(topic_scores, key=lambda item: float(item.score))
        ]

        weak_topics = [item for item in heatmap if item["score"] < 72][:5]
        weakness_analysis = self.weakness_engine.analyze(
            topic_scores={int(score.topic_id): float(score.score) for score in topic_scores},
            prerequisite_map=prerequisite_map,
            confidence_by_topic={int(score.topic_id): float(score.confidence) for score in topic_scores},
            retention_by_topic={int(score.topic_id): float(score.retention_score) for score in topic_scores},
        )

        focus_score = round(
            min(
                100.0,
                max(
                    0.0,
                    float(user.focus_score)
                    or (
                        (completion_percent * 0.35)
                        + (min(streak, 7) * 6)
                        + (sum(item["score"] for item in heatmap) / max(len(heatmap), 1) * 0.35)
                    ),
                ),
            ),
            1,
        )

        skill_nodes = []
        unlocked_topic_ids = {int(score.topic_id) for score in topic_scores if float(score.score) >= 70.0}
        unlocked_topic_ids |= {
            int(step.topic_id) for step in steps if str(step.progress_status).lower() == "completed"
        }
        for topic_id, topic_name in topic_names.items():
            prerequisites = prerequisite_map.get(topic_id, [])
            status = "locked"
            if topic_id in unlocked_topic_ids:
                status = "mastered"
            elif all(prerequisite in unlocked_topic_ids for prerequisite in prerequisites):
                status = "available"
            skill_nodes.append(
                {
                    "topic_id": topic_id,
                    "topic_name": topic_name,
                    "status": status,
                    "dependencies": prerequisites,
                }
            )

        leaderboard_result = await self.session.execute(
            select(User.id, User.display_name, User.email, User.experience_points)
            .join(UserTenantRole, UserTenantRole.user_id == User.id)
            .where(
                UserTenantRole.tenant_id == tenant_id,
                UserTenantRole.role == UserRole.student,
            )
            .order_by(User.experience_points.desc(), User.id.asc())
            .limit(10)
        )
        leaderboard = []
        for rank, row in enumerate(leaderboard_result.all(), start=1):
            leaderboard.append(
                {
                    "rank": rank,
                    "user_id": int(row.id),
                    "name": row.display_name or row.email.split("@")[0],
                    "xp": int(row.experience_points or 0),
                    "is_current_user": int(row.id) == user_id,
                }
            )

        retention_summary = await self.retention_service.learner_retention_summary(
            tenant_id=tenant_id,
            user_id=user_id,
        )
        profile = self.learning_profile_engine.analyze(
            response_times=[max(12.0, point["minutes"]) for point in velocity_points if point["minutes"] > 0] or [24.0],
            accuracies=[float(item["score"]) for item in heatmap] or [50.0],
            difficulty_distribution={"easy": 2, "medium": 4, "hard": max(1, len(heatmap) // 3)},
        )
        cognitive_model = self.cognitive_modeling_service.build_model(
            topic_scores={int(score.topic_id): float(score.score) for score in topic_scores},
            response_times=[max(12.0, point["minutes"]) for point in velocity_points if point["minutes"] > 0],
            accuracies=[float(item["score"]) for item in heatmap],
            learning_profile={
                "profile_type": profile.profile_type,
                "confidence": profile.confidence,
                "speed": profile.speed,
                "accuracy": profile.accuracy,
                "consistency": profile.consistency,
                "stamina": profile.stamina,
            },
            past_mistakes=[],
        )

        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "completion_percent": completion_percent,
            "streak_days": streak,
            "focus_score": focus_score,
            "xp": int(user.experience_points or 0),
            "roadmap_progress": {
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "in_progress_steps": in_progress_steps,
                "completion_percent": completion_percent,
            },
            "learning_velocity": velocity_points,
            "weak_topic_heatmap": heatmap,
            "weak_topics": weak_topics,
            "weakness_clusters": weakness_analysis["weakness_clusters"],
            "learning_profile": {
                "profile_type": profile.profile_type,
                "confidence": profile.confidence,
                "speed": profile.speed,
                "accuracy": profile.accuracy,
                "consistency": profile.consistency,
                "stamina": profile.stamina,
            },
            "cognitive_model": cognitive_model,
            "mentor_suggestions": [
                {
                    "id": int(item.id),
                    "title": item.title,
                    "message": item.message,
                    "why": item.why_reason,
                    "topic_id": item.topic_id,
                    "is_ai_generated": item.is_ai_generated,
                }
                for item in suggestions
            ],
            "retention": retention_summary,
            "skill_graph": skill_nodes,
            "gamification": {
                "badges": [
                    {
                        "name": badge.name,
                        "description": badge.description,
                        "awarded_at": badge.awarded_at.isoformat(),
                    }
                    for badge in badges[:6]
                ],
                "leaderboard": leaderboard,
            },
            "recent_activity": [
                {
                    "event_type": event.event_type,
                    "created_at": event.created_at.isoformat(),
                    "topic_id": event.topic_id,
                }
                for event in learning_events[:8]
            ],
        }

    async def teacher_analytics(self, *, tenant_id: int) -> dict:
        topic_names = await self._topic_name_map(tenant_id)

        score_rows_result = await self.session.execute(select(TopicScore).where(TopicScore.tenant_id == tenant_id))
        score_rows = score_rows_result.scalars().all()

        by_user: dict[int, list[TopicScore]] = defaultdict(list)
        by_topic: dict[int, list[float]] = defaultdict(list)
        for row in score_rows:
            by_user[int(row.user_id)].append(row)
            by_topic[int(row.topic_id)].append(float(row.score))

        students_result = await self.session.execute(
            select(User.id, User.display_name, User.email, User.experience_points)
            .where(user_has_tenant_role(User, tenant_id, UserRole.student.value))
            .order_by(User.email.asc())
        )
        students = students_result.all()
        roadmap_progress = {
            int(item["user_id"]): item
            for item in await self.analytics_service._roadmap_progress_rows(tenant_id)
        }

        roadmap_rows = []
        for student in students:
            user_id = int(student.id)
            progress = roadmap_progress.get(user_id, {})
            completion_percent = float(progress.get("completion_percent", 0.0))
            avg_score = round(
                sum(float(score.score) for score in by_user.get(user_id, [])) / max(len(by_user.get(user_id, [])), 1),
                2,
            ) if by_user.get(user_id) else 0.0
            risk_level = "low"
            if completion_percent < 35 or avg_score < 55:
                risk_level = "critical"
            elif completion_percent < 60 or avg_score < 70:
                risk_level = "watch"

            roadmap_rows.append(
                {
                    "user_id": user_id,
                    "name": student.display_name or student.email.split("@")[0],
                    "email": student.email,
                    "completion_percent": completion_percent,
                    "average_score": avg_score,
                    "risk_level": risk_level,
                    "xp": int(student.experience_points or 0),
                }
            )

        weak_clusters = [
            {
                "topic_id": topic_id,
                "topic_name": topic_names.get(topic_id, f"Topic {topic_id}"),
                "average_score": round(sum(values) / len(values), 2),
                "student_count": len(values),
            }
            for topic_id, values in by_topic.items()
        ]
        weak_clusters.sort(key=lambda item: item["average_score"])

        performance_distribution = {
            "critical": sum(1 for item in roadmap_rows if item["risk_level"] == "critical"),
            "watch": sum(1 for item in roadmap_rows if item["risk_level"] == "watch"),
            "strong": sum(1 for item in roadmap_rows if item["risk_level"] == "low"),
        }

        sorted_students = sorted(roadmap_rows, key=lambda item: (item["completion_percent"], item["average_score"]))
        top_students = list(reversed(sorted_students[-3:]))
        bottom_students = sorted_students[:3]
        risk_students = [item for item in roadmap_rows if item["risk_level"] != "low"][:5]

        return {
            "tenant_id": tenant_id,
            "student_count": len(roadmap_rows),
            "weak_topic_clusters": weak_clusters[:8],
            "performance_distribution": performance_distribution,
            "top_students": top_students,
            "bottom_students": bottom_students,
            "risk_students": risk_students,
        }

    async def experiment_summary(self, *, tenant_id: int) -> dict:
        experiments_result = await self.session.execute(
            select(Experiment).where(Experiment.tenant_id == tenant_id).order_by(Experiment.created_at.desc())
        )
        experiments = experiments_result.scalars().all()
        items = []
        for experiment in experiments:
            variants_result = await self.session.execute(
                select(ExperimentVariant)
                .where(ExperimentVariant.experiment_id == experiment.id)
                .order_by(ExperimentVariant.id.asc())
            )
            variants = variants_result.scalars().all()
            items.append(
                {
                    "id": int(experiment.id),
                    "key": experiment.key,
                    "name": experiment.name,
                    "status": experiment.status,
                    "success_metric": experiment.success_metric,
                    "variants": [
                        {
                            "id": int(variant.id),
                            "name": variant.name,
                            "population_size": int(variant.population_size),
                            "conversion_rate": round(float(variant.conversion_rate), 2),
                            "engagement_lift": round(float(variant.engagement_lift), 2),
                        }
                        for variant in variants
                    ],
                }
            )
        return {"tenant_id": tenant_id, "experiments": items}

    async def community_summary(self, *, tenant_id: int) -> dict:
        communities_result = await self.session.execute(
            select(Community).where(Community.tenant_id == tenant_id).order_by(Community.created_at.desc())
        )
        threads_result = await self.session.execute(
            select(DiscussionThread).where(DiscussionThread.tenant_id == tenant_id).order_by(DiscussionThread.created_at.desc())
        )
        replies_result = await self.session.execute(
            select(DiscussionReply).where(DiscussionReply.tenant_id == tenant_id).order_by(DiscussionReply.created_at.desc())
        )
        communities = communities_result.scalars().all()
        threads = threads_result.scalars().all()
        replies = replies_result.scalars().all()

        return {
            "tenant_id": tenant_id,
            "community_count": len(communities),
            "thread_count": len(threads),
            "resolved_threads": sum(1 for thread in threads if bool(thread.is_resolved)),
            "best_answers": sum(1 for reply in replies if bool(reply.is_best_answer)),
            "ai_assisted_answers": sum(1 for reply in replies if bool(reply.is_ai_assisted)),
        }
