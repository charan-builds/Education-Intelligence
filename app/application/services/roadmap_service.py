from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import decode_cursor, encode_cursor
from app.core.feature_flags import FeatureFlagService
from app.domain.engines.knowledge_graph import KnowledgeGraphEngine
from app.domain.engines.learning_profile_engine import LearningProfileEngine
from app.domain.engines.weakness_modeling_engine import WeaknessModelingEngine
from app.domain.engines.topic_difficulty_engine import TopicDifficultyEngine
from app.application.services.recommendation_service import RecommendationService
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.repositories.diagnostic_repository import DiagnosticRepository
from app.infrastructure.repositories.roadmap_repository import RoadmapRepository
from app.infrastructure.repositories.topic_repository import TopicRepository
from app.application.exceptions import NotFoundError
from app.application.exceptions import ValidationError
from app.application.services.learning_event_service import LearningEventService
from app.application.services.gamification_service import GamificationService
from app.application.services.learning_intelligence_service import LearningIntelligenceService
from app.application.services.ml_platform_service import MLPlatformService
from app.application.services.retention_service import RetentionService
from app.application.services.skill_vector_service import SkillVectorService
from app.application.services.notification_service import NotificationService
from app.application.services.outbox_service import OutboxService

class RoadmapService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.roadmap_repository = RoadmapRepository(session)
        self.topic_repository = TopicRepository(session)
        self.diagnostic_repository = DiagnosticRepository(session)
        self.recommendation_service = RecommendationService()
        self.learning_profile_engine = LearningProfileEngine()
        self.weakness_engine = WeaknessModelingEngine()
        self.topic_difficulty_engine = TopicDifficultyEngine()
        self.cache_service = CacheService()
        self.feature_flag_service = FeatureFlagService(session)
        self.learning_event_service = LearningEventService(session)
        self.gamification_service = GamificationService(session)
        self.notification_service = NotificationService(session)
        self.retention_service = RetentionService(session)
        self.skill_vector_service = SkillVectorService(session)
        self.ml_platform_service = MLPlatformService(session)
        self.outbox_service = OutboxService(session)

    async def _update_gamification_state(self, *, user_id: int, tenant_id: int, completed_step: bool) -> None:
        if not completed_step:
            return
        await self.gamification_service.get_profile(tenant_id=tenant_id, user_id=user_id)

    @staticmethod
    def _phase_label(priority: int, total_steps: int) -> str:
        if total_steps <= 0:
            return "Phase 1 - Foundations"
        chunk_size = max(1, (total_steps + 2) // 3)
        if priority <= chunk_size:
            return "Phase 1 - Foundations"
        if priority <= chunk_size * 2:
            return "Phase 2 - Intermediate Skills"
        return "Phase 3 - Advanced Specialization"

    def _serialize_roadmap(self, roadmap, total_steps: int) -> dict:
        return {
            "id": roadmap.id,
            "user_id": roadmap.user_id,
            "goal_id": roadmap.goal_id,
            "test_id": roadmap.test_id,
            "status": roadmap.status,
            "error_message": roadmap.error_message,
            "generated_at": roadmap.generated_at.isoformat(),
            "steps": [
                {
                    "id": step.id,
                    "topic_id": step.topic_id,
                    "phase": self._phase_label(step.priority, total_steps),
                    "estimated_time_hours": step.estimated_time_hours,
                    "difficulty": step.difficulty,
                    "priority": step.priority,
                    "deadline": step.deadline.isoformat(),
                    "progress_status": step.progress_status,
                    "step_type": getattr(step, "step_type", "core"),
                    "rationale": getattr(step, "rationale", None),
                    "unlocks_topic_id": getattr(step, "unlocks_topic_id", None),
                    "is_revision": bool(getattr(step, "is_revision", False)),
                }
                for step in roadmap.steps
            ],
        }

    def serialize_roadmap(self, roadmap) -> dict:
        return self._serialize_roadmap(roadmap, len(getattr(roadmap, "steps", []) or []))

    async def get_for_test(self, user_id: int, tenant_id: int, goal_id: int, test_id: int):
        return await self.roadmap_repository.get_by_identity(
            user_id=user_id,
            goal_id=goal_id,
            test_id=test_id,
            tenant_id=tenant_id,
        )

    async def ensure_generation_requested(
        self,
        user_id: int,
        tenant_id: int,
        goal_id: int,
        test_id: int,
    ) -> tuple[object, bool]:
        async def _reload_for_response():
            loaded = await self.roadmap_repository.get_by_identity(
                user_id=user_id,
                goal_id=goal_id,
                test_id=test_id,
                tenant_id=tenant_id,
            )
            return loaded

        existing = await self.get_for_test(user_id=user_id, tenant_id=tenant_id, goal_id=goal_id, test_id=test_id)
        if existing is not None:
            if existing.status in {"generating", "ready"}:
                return existing, False
            await self.roadmap_repository.mark_status(existing, status="generating", error_message=None)
            await self.session.commit()
            return (await _reload_for_response()) or existing, True
        try:
            roadmap = await self.roadmap_repository.create_roadmap(
                user_id=user_id,
                goal_id=goal_id,
                test_id=test_id,
                generated_at=datetime.now(timezone.utc),
                status="generating",
            )
            await self.session.commit()
            return (await _reload_for_response()) or roadmap, True
        except IntegrityError:
            await self.session.rollback()
            existing = await self.get_for_test(user_id=user_id, tenant_id=tenant_id, goal_id=goal_id, test_id=test_id)
            if existing is None:
                raise
            return existing, existing.status not in {"generating", "ready"}
        except Exception:
            await self.session.rollback()
            raise

    async def generate(self, user_id: int, tenant_id: int, goal_id: int, test_id: int):
        try:
            roadmap = await self.roadmap_repository.get_by_identity(
                user_id=user_id,
                goal_id=goal_id,
                test_id=test_id,
                tenant_id=tenant_id,
                for_update=True,
            )
            if roadmap is None:
                roadmap = await self.roadmap_repository.create_roadmap(
                    user_id=user_id,
                    goal_id=goal_id,
                    test_id=test_id,
                    generated_at=datetime.now(timezone.utc),
                    status="generating",
                )
            elif roadmap.status == "ready" and roadmap.steps:
                return roadmap
            elif roadmap.status == "generating" and roadmap.steps:
                return roadmap
            else:
                await self.roadmap_repository.clear_steps(roadmap)
                await self.roadmap_repository.mark_status(roadmap, status="generating", error_message=None)

            topic_scores = await self.diagnostic_repository.topic_scores_for_test(test_id, user_id, tenant_id)
            if not topic_scores:
                raise NotFoundError("Diagnostic result not found or unauthorized")

            prerequisite_edges = await self.topic_repository.get_prerequisite_edges(tenant_id=tenant_id)

            analytics = {"response_times": [], "accuracies": [], "difficulty_distribution": {}}
            if hasattr(self.diagnostic_repository, "answer_analytics_for_test"):
                analytics = await self.diagnostic_repository.answer_analytics_for_test(  # type: ignore[attr-defined]
                    test_id=test_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                )

            profile = self.learning_profile_engine.analyze(
                response_times=analytics.get("response_times", []),
                accuracies=analytics.get("accuracies", []),
                difficulty_distribution=analytics.get("difficulty_distribution", {}),
            )
            user_learning_profile = {
                "profile_type": profile.profile_type,
                "confidence": profile.confidence,
                "speed": profile.speed,
                "accuracy": profile.accuracy,
                "consistency": profile.consistency,
                "stamina": profile.stamina,
            }
            goal_context = {"goal_id": goal_id}
            try:
                ml_enabled = await self.feature_flag_service.is_enabled("ml_recommendation_enabled", tenant_id)
            except Exception:
                ml_enabled = False

            recommended_targets = await self.recommendation_service.weak_topics_with_foundations_async(
                topic_scores=topic_scores,
                prerequisite_edges=prerequisite_edges,
                user_id=user_id,
                tenant_id=tenant_id,
                learning_profile=user_learning_profile,
                goal=goal_context,
                feature_flags={"ml_recommendation_enabled": ml_enabled},
            )
            prerequisite_map: dict[int, list[int]] = {}
            for topic_id, prerequisite_topic_id in prerequisite_edges:
                prerequisite_map.setdefault(int(topic_id), []).append(int(prerequisite_topic_id))
            weakness_analysis = self.weakness_engine.analyze(
                topic_scores={int(topic_id): float(score) for topic_id, score in topic_scores.items()},
                prerequisite_map=prerequisite_map,
            )
            for cluster in weakness_analysis["weakness_clusters"]:
                for topic_id in cluster["topic_ids"]:
                    if topic_id not in recommended_targets:
                        recommended_targets.append(int(topic_id))

            knowledge_graph_engine = KnowledgeGraphEngine(self.topic_repository)
            topic_order: list[int] = []
            seen: set[int] = set()
            topic_paths = await knowledge_graph_engine.generate_learning_paths(recommended_targets, tenant_id=tenant_id)
            for target_topic in recommended_targets:
                path = topic_paths.get(int(target_topic), [int(target_topic)])
                for topic_id in path:
                    if topic_id not in seen:
                        topic_order.append(topic_id)
                        seen.add(topic_id)

            if not topic_order:
                topic_order = sorted(topic_scores.keys())

            dependency_depths = await knowledge_graph_engine.get_dependency_depths(topic_order, tenant_id=tenant_id)
            base_date = datetime.now(timezone.utc)
            days_per_step = 7
            if profile.profile_type == "slow_deep_learner":
                days_per_step = 10
            elif profile.profile_type == "practice_focused":
                days_per_step = 5

            avg_time = analytics.get("response_times", [])
            time_factor = min(1.0, (sum(avg_time) / len(avg_time)) / 60) if avg_time else 0.5

            profile_time_multiplier = 1.0
            if profile.profile_type == "slow_deep_learner":
                profile_time_multiplier = 1.4
            elif profile.profile_type == "practice_focused":
                profile_time_multiplier = 0.85
            elif profile.profile_type == "concept_focused":
                profile_time_multiplier = 1.15

            base_hours_by_difficulty = {"easy": 2.0, "medium": 4.0, "hard": 6.0, "expert": 8.0}
            for index, topic_id in enumerate(topic_order):
                topic_score = float(topic_scores.get(topic_id, 50.0))
                inverse_score = max(0.0, min(1.0, 1 - (topic_score / 100)))
                difficulty_result = self.topic_difficulty_engine.evaluate(
                    failure_rate=inverse_score,
                    time_factor=time_factor,
                    score_factor=inverse_score,
                )
                dependency_depth = dependency_depths.get(int(topic_id), 0)
                estimated_time_hours = round(
                    base_hours_by_difficulty[difficulty_result.level]
                    * profile_time_multiplier
                    * (1 + (dependency_depth * 0.1)),
                    2,
                )
                clustered = any(topic_id in cluster["topic_ids"] for cluster in weakness_analysis["weakness_clusters"])
                await self.roadmap_repository.add_step(
                    roadmap_id=roadmap.id,
                    topic_id=topic_id,
                    estimated_time_hours=estimated_time_hours,
                    difficulty=difficulty_result.level,
                    priority=index + 1,
                    deadline=base_date + timedelta(days=days_per_step * (index + 1)),
                    step_type="core",
                    rationale=(
                        "Scheduled early to stabilize a weakness cluster and unblock downstream mastery."
                        if clustered
                        else "Scheduled from diagnostic gaps, dependency depth, and learning profile analysis."
                    ),
                )

            await self.roadmap_repository.mark_status(roadmap, status="ready", error_message=None)
            roadmap.generated_at = datetime.now(timezone.utc)
            await self.learning_event_service.track_roadmap_generated(
                tenant_id=tenant_id,
                user_id=user_id,
                diagnostic_test_id=test_id,
                goal_id=goal_id,
                roadmap_id=int(roadmap.id),
                idempotency_key=f"roadmap-generated:{tenant_id}:{user_id}:{goal_id}:{test_id}",
                commit=False,
            )
            await self.session.commit()
            await self.cache_service.bump_namespace_version("analytics:overview")
            await self.cache_service.bump_namespace_version("analytics:topic-mastery")
            await self.cache_service.bump_namespace_version("analytics:roadmap-progress")
            await self.outbox_service.add_task_event(
                task_name="jobs.refresh_precomputed_analytics",
                args=[tenant_id],
                tenant_id=tenant_id,
                idempotency_key=f"refresh-precomputed:roadmap-generated:{tenant_id}:{user_id}:{goal_id}:{test_id}",
            )
            await self.outbox_service.add_task_event(
                task_name="jobs.generate_notifications",
                args=[tenant_id, 100],
                tenant_id=tenant_id,
                idempotency_key=f"generate-notifications:roadmap-generated:{tenant_id}:{user_id}:{goal_id}:{test_id}",
            )
            await self.notification_service.create_notification(
                tenant_id=tenant_id,
                user_id=user_id,
                notification_type="roadmap_generated",
                severity="info",
                title="Roadmap ready",
                message="Your latest roadmap is ready to review.",
                action_url="/student/roadmap",
                dedupe_key=f"roadmap-generated:{tenant_id}:{user_id}:{goal_id}:{test_id}",
            )
            loaded_roadmap = await self.roadmap_repository.get_roadmap_for_user(
                roadmap_id=roadmap.id,
                user_id=user_id,
                tenant_id=tenant_id,
            )
            if loaded_roadmap is None:
                raise NotFoundError("Generated roadmap could not be reloaded")
            return loaded_roadmap
        except Exception as exc:
            await self.session.rollback()
            if "roadmap" in locals() and roadmap is not None:
                try:
                    failed_roadmap = await self.roadmap_repository.get_by_identity(
                        user_id=user_id,
                        goal_id=goal_id,
                        test_id=test_id,
                        tenant_id=tenant_id,
                    )
                    if failed_roadmap is not None:
                        await self.roadmap_repository.clear_steps(failed_roadmap)
                        await self.roadmap_repository.mark_status(
                            failed_roadmap,
                            status="failed",
                            error_message=str(exc)[:500],
                        )
                        await self.session.commit()
                except Exception:
                    await self.session.rollback()
            raise

    async def list_for_user(self, user_id: int, tenant_id: int, limit: int, offset: int):
        return await self.roadmap_repository.list_user_roadmaps(
            user_id=user_id,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )

    async def list_for_user_page(
        self,
        user_id: int,
        tenant_id: int,
        limit: int,
        offset: int,
        cursor: str | None = None,
    ) -> dict:
        try:
            cursor_id = decode_cursor(cursor) if cursor else None
        except ValueError as exc:
            raise ValidationError("Invalid cursor") from exc

        cache_cursor = cursor if cursor is not None else "none"
        cache_key = await self.cache_service.build_versioned_key(
            f"roadmap:user:{tenant_id}:{user_id}",
            limit=limit,
            offset=offset,
            cursor=cache_cursor,
        )
        cached = await self.cache_service.get(cache_key)
        if isinstance(cached, dict):
            return cached

        items = await self.roadmap_repository.list_user_roadmaps(
            user_id=user_id,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
            cursor_id=cursor_id,
        )
        total = await self.roadmap_repository.count_user_roadmaps(user_id=user_id, tenant_id=tenant_id)
        next_cursor = encode_cursor(items[-1].id) if items and len(items) == limit else None
        next_offset = offset + limit if (offset + limit) < total else None
        payload = {
            "items": items,
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "next_cursor": next_cursor,
            },
        }
        serialized_payload = {
            "items": [self._serialize_roadmap(roadmap, len(roadmap.steps)) for roadmap in items],
            "meta": payload["meta"],
        }
        await self.cache_service.set(cache_key, serialized_payload, ttl=300)
        return serialized_payload

    async def update_step_status(
        self,
        *,
        step_id: int,
        user_id: int,
        tenant_id: int,
        progress_status: str,
    ) -> dict:
        normalized_status = progress_status.strip().lower()
        allowed_statuses = {"pending", "in_progress", "completed"}
        if normalized_status not in allowed_statuses:
            raise ValidationError("Invalid roadmap step status")

        step = await self.roadmap_repository.get_step_for_user(step_id=step_id, user_id=user_id, tenant_id=tenant_id)
        if step is None:
            raise NotFoundError("Roadmap step not found")
        previous_status = str(step.progress_status).lower()

        await self.roadmap_repository.update_step_status(step, progress_status=normalized_status)
        await self.learning_event_service.track_learning_action(
            tenant_id=tenant_id,
            user_id=user_id,
            action_type="complete" if normalized_status == "completed" else "view" if normalized_status == "in_progress" else "skip",
            topic_id=step.topic_id,
            time_spent_seconds=int(step.estimated_time_hours * 3600) if normalized_status == "completed" else None,
            metadata={"step_id": step.id, "progress_status": normalized_status},
            commit=False,
        )
        await self.skill_vector_service.update_from_progress(
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=step.topic_id,
            progress_status=normalized_status,
            observed_at=datetime.now(timezone.utc),
        )
        if normalized_status == "completed" and previous_status != "completed":
            await self.gamification_service.award_topic_completion(
                tenant_id=tenant_id,
                user_id=user_id,
                topic_id=int(step.topic_id),
                roadmap_step_id=int(step.id),
                activity_time=datetime.now(timezone.utc),
            )
        await self.session.commit()

        if normalized_status == "completed":
            await self.learning_event_service.track_topic_completed(
                tenant_id=tenant_id,
                user_id=user_id,
                topic_id=step.topic_id,
                completion_score=100.0,
                commit=False,
            )
            await self.retention_service.schedule_topic_review(
                tenant_id=tenant_id,
                user_id=user_id,
                topic_id=step.topic_id,
                completion_score=100.0,
            )
            await self.ml_platform_service.build_feature_snapshot(user_id=user_id, tenant_id=tenant_id)
        else:
            await self.session.commit()

        await self.cache_service.bump_namespace_version(f"roadmap:user:{tenant_id}:{user_id}")
        await self.cache_service.bump_namespace_version("analytics:overview")
        await self.cache_service.bump_namespace_version("analytics:topic-mastery")
        await self.cache_service.bump_namespace_version("analytics:roadmap-progress")
        await self.outbox_service.add_task_event(
            task_name="jobs.refresh_precomputed_analytics",
            args=[tenant_id],
            tenant_id=tenant_id,
            idempotency_key=f"refresh-precomputed:roadmap-step:{tenant_id}:{user_id}:{step_id}:{normalized_status}",
        )
        await self.outbox_service.add_task_event(
            task_name="jobs.generate_notifications",
            args=[tenant_id, 100],
            tenant_id=tenant_id,
            idempotency_key=f"generate-notifications:roadmap-step:{tenant_id}:{user_id}:{step_id}:{normalized_status}",
        )
        await self.session.commit()
        return {
            "id": step.id,
            "topic_id": step.topic_id,
            "phase": None,
            "estimated_time_hours": step.estimated_time_hours,
            "difficulty": step.difficulty,
            "priority": step.priority,
            "deadline": step.deadline,
            "progress_status": step.progress_status,
            "step_type": getattr(step, "step_type", "core"),
            "rationale": getattr(step, "rationale", None),
            "unlocks_topic_id": getattr(step, "unlocks_topic_id", None),
            "is_revision": bool(getattr(step, "is_revision", False)),
        }

    async def adapt_latest(self, *, user_id: int, tenant_id: int) -> dict:
        result = await LearningIntelligenceService(self.session).adaptive_refresh(
            user_id=user_id,
            tenant_id=tenant_id,
        )
        await self.cache_service.bump_namespace_version(f"roadmap:user:{tenant_id}:{user_id}")
        return result
