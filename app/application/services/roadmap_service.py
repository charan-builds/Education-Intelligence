from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import decode_cursor, encode_cursor
from app.core.feature_flags import FeatureFlagService
from app.domain.engines.knowledge_graph import KnowledgeGraphEngine
from app.domain.engines.learning_profile_engine import LearningProfileEngine
from app.domain.engines.topic_difficulty_engine import TopicDifficultyEngine
from app.application.services.recommendation_service import RecommendationService
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.repositories.diagnostic_repository import DiagnosticRepository
from app.infrastructure.repositories.roadmap_repository import RoadmapRepository
from app.infrastructure.repositories.topic_repository import TopicRepository
from app.application.exceptions import NotFoundError
from app.application.exceptions import ValidationError


class RoadmapService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.roadmap_repository = RoadmapRepository(session)
        self.topic_repository = TopicRepository(session)
        self.diagnostic_repository = DiagnosticRepository(session)
        self.recommendation_service = RecommendationService()
        self.learning_profile_engine = LearningProfileEngine()
        self.topic_difficulty_engine = TopicDifficultyEngine()
        self.cache_service = CacheService()
        self.feature_flag_service = FeatureFlagService(session)

    async def generate(self, user_id: int, tenant_id: int, goal_id: int, test_id: int):
        try:
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

            knowledge_graph_engine = KnowledgeGraphEngine(self.topic_repository)
            topic_order: list[int] = []
            seen: set[int] = set()
            for target_topic in recommended_targets:
                path = await knowledge_graph_engine.generate_learning_path(
                    target_topic_id=target_topic,
                    tenant_id=tenant_id,
                )
                for topic_id in path:
                    if topic_id not in seen:
                        topic_order.append(topic_id)
                        seen.add(topic_id)

            if not topic_order:
                topic_order = sorted(topic_scores.keys())

            roadmap = await self.roadmap_repository.create_roadmap(
                user_id=user_id,
                goal_id=goal_id,
                generated_at=datetime.now(timezone.utc),
            )
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
                dependency_depth = await knowledge_graph_engine.get_dependency_depth(topic_id, tenant_id)
                estimated_time_hours = round(
                    base_hours_by_difficulty[difficulty_result.level]
                    * profile_time_multiplier
                    * (1 + (dependency_depth * 0.1)),
                    2,
                )
                await self.roadmap_repository.add_step(
                    roadmap_id=roadmap.id,
                    topic_id=topic_id,
                    estimated_time_hours=estimated_time_hours,
                    difficulty=difficulty_result.level,
                    priority=index + 1,
                    deadline=base_date + timedelta(days=days_per_step * (index + 1)),
                )

            await self.session.commit()
            return roadmap
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
        cache_key = (
            f"tenant:{tenant_id}:roadmap:{user_id}:limit:{limit}:offset:{offset}:cursor:{cache_cursor}"
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
            "items": [
                {
                    "id": roadmap.id,
                    "user_id": roadmap.user_id,
                    "goal_id": roadmap.goal_id,
                    "generated_at": roadmap.generated_at.isoformat(),
                    "steps": [
                        {
                            "id": step.id,
                            "topic_id": step.topic_id,
                            "estimated_time_hours": step.estimated_time_hours,
                            "difficulty": step.difficulty,
                            "priority": step.priority,
                            "deadline": step.deadline.isoformat(),
                            "progress_status": step.progress_status,
                        }
                        for step in roadmap.steps
                    ],
                }
                for roadmap in items
            ],
            "meta": payload["meta"],
        }
        await self.cache_service.set(cache_key, serialized_payload, ttl=300)
        return payload
