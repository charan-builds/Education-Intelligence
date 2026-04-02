import json

from app.core.config import get_settings
from app.domain.engines.ml_recommendation_engine import MLRecommendationEngine, RankedTopicRecommendation
from app.domain.engines.recommendation_engine import RecommendationEngine
from app.domain.engines.rule_engine import RuleEngine
from app.infrastructure.repositories.ai_request_repository import AIRequestRepository
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.ai_request_service import AIRequestService


def build_recommendation_engine(engine_name: str) -> RecommendationEngine:
    if engine_name.lower() == "ml":
        return MLRecommendationEngine()
    return RuleEngine()


class RecommendationService:
    def __init__(self, engine: RecommendationEngine | None = None, session: AsyncSession | None = None):
        self.session = session
        if engine is not None:
            self.engine = engine
            return

        settings = get_settings()
        self.engine = build_recommendation_engine(settings.recommendation_engine)

    async def _get_async_learning_path_result(
        self,
        *,
        user_id: int,
        tenant_id: int,
        goal_name: str,
        topic_scores: dict[int, float],
        prerequisite_edges: list[tuple[int, int]],
        learning_profile: dict | None,
    ) -> list[int]:
        if self.session is None or not hasattr(self.session, "execute"):
            return []

        request_service = AIRequestService(self.session)
        queued = await request_service.queue_learning_path_recommendation(
            tenant_id=tenant_id,
            user_id=user_id,
            goal=goal_name,
            topic_scores=topic_scores,
            prerequisites=prerequisite_edges,
            learning_profile=learning_profile,
        )
        if queued.get("status") not in {"completed", "fallback"}:
            repository = AIRequestRepository(self.session)
            row = await repository.get_by_request_id(
                tenant_id=tenant_id,
                user_id=user_id,
                request_id=str(queued["request_id"]),
            )
            if row is None or row.status not in {"completed", "fallback"} or not row.result_json:
                return []
            try:
                result_payload = json.loads(row.result_json)
            except json.JSONDecodeError:
                return []
        else:
            result = await request_service.get_result(
                tenant_id=tenant_id,
                user_id=user_id,
                request_id=str(queued["request_id"]),
            )
            if not result:
                return []
            result_payload = dict(result.get("result") or {})

        raw_steps = result_payload.get("recommended_steps", [])
        if not isinstance(raw_steps, list):
            return []
        return [
            int(step.get("topic_id"))
            for step in raw_steps
            if isinstance(step, dict) and step.get("topic_id") is not None
        ]

    def classify_topics(self, topic_scores: dict[int, float]) -> dict[int, str]:
        return {topic_id: self.engine.classify_topic(score) for topic_id, score in topic_scores.items()}

    def rank_topics(
        self,
        *,
        topic_scores: dict[int, float],
        prerequisite_edges: list[tuple[int, int]],
        learning_profile: dict | None = None,
        goal: dict | None = None,
    ) -> list[RankedTopicRecommendation]:
        if isinstance(self.engine, MLRecommendationEngine):
            return self.engine.rank_topics(
                topic_scores=topic_scores,
                prerequisite_edges=prerequisite_edges,
                learning_profile=learning_profile,
                goal=goal,
            )
        ordered_ids = self.engine.recommend_roadmap_steps(
            topic_scores=topic_scores,
            prerequisite_edges=prerequisite_edges,
            learning_profile=learning_profile,
            goal=goal,
        )
        return [
            RankedTopicRecommendation(
                topic_id=topic_id,
                priority_score=float(max(0.0, 100.0 - topic_scores.get(topic_id, 100.0))),
                explanation="Rule engine fallback prioritized this topic from weak mastery and prerequisites.",
            )
            for topic_id in ordered_ids
        ]

    def weak_topics_with_foundations(
        self,
        topic_scores: dict[int, float],
        prerequisite_edges: list[tuple[int, int]],
        learning_profile: dict | None = None,
        goal: dict | None = None,
        feature_flags: dict[str, bool] | None = None,
    ) -> list[int]:
        selected_engine = self.engine
        flags = feature_flags or {}
        if not flags.get("ml_recommendation_enabled", True):
            selected_engine = RuleEngine()
        return selected_engine.recommend_roadmap_steps(
            topic_scores=topic_scores,
            prerequisite_edges=prerequisite_edges,
            learning_profile=learning_profile,
            goal=goal,
        )

    async def weak_topics_with_foundations_async(
        self,
        topic_scores: dict[int, float],
        prerequisite_edges: list[tuple[int, int]],
        *,
        user_id: int,
        tenant_id: int,
        learning_profile: dict | None = None,
        goal: dict | None = None,
        feature_flags: dict[str, bool] | None = None,
    ) -> list[int]:
        flags = feature_flags or {}
        ml_enabled = flags.get("ml_recommendation_enabled", False)

        if ml_enabled:
            goal_name = str((goal or {}).get("goal_name") or (goal or {}).get("goal_id") or "default_goal")
            ai_topics = await self._get_async_learning_path_result(
                user_id=user_id,
                tenant_id=tenant_id,
                goal_name=goal_name,
                topic_scores=topic_scores,
                prerequisite_edges=prerequisite_edges,
                learning_profile=learning_profile,
            )
            if ai_topics:
                return ai_topics

        return self.weak_topics_with_foundations(
            topic_scores=topic_scores,
            prerequisite_edges=prerequisite_edges,
            learning_profile=learning_profile,
            goal=goal,
            feature_flags={"ml_recommendation_enabled": False},
        )
