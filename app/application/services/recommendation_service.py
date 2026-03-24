from app.core.config import get_settings
from app.domain.engines.ml_recommendation_engine import MLRecommendationEngine
from app.domain.engines.recommendation_engine import RecommendationEngine
from app.domain.engines.rule_engine import RuleEngine
from app.infrastructure.clients.ai_service_client import AIServiceClient


def build_recommendation_engine(engine_name: str) -> RecommendationEngine:
    if engine_name.lower() == "ml":
        return MLRecommendationEngine()
    return RuleEngine()


class RecommendationService:
    def __init__(self, engine: RecommendationEngine | None = None):
        self.ai_service_client = AIServiceClient()
        if engine is not None:
            self.engine = engine
            return

        settings = get_settings()
        self.engine = build_recommendation_engine(settings.recommendation_engine)

    def classify_topics(self, topic_scores: dict[int, float]) -> dict[int, str]:
        return {topic_id: self.engine.classify_topic(score) for topic_id, score in topic_scores.items()}

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
            try:
                goal_name = str((goal or {}).get("goal_name") or (goal or {}).get("goal_id") or "default_goal")
                ai_response = await self.ai_service_client.predict_learning_path(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    goal=goal_name,
                    topic_scores=topic_scores,
                    prerequisites=prerequisite_edges,
                    learning_profile=learning_profile or {},
                )
                raw_steps = ai_response.get("recommended_steps", [])
                if isinstance(raw_steps, list):
                    ai_topics = [
                        int(step.get("topic_id"))
                        for step in raw_steps
                        if isinstance(step, dict) and step.get("topic_id") is not None
                    ]
                    if ai_topics:
                        return ai_topics
            except Exception:
                pass

        return self.weak_topics_with_foundations(
            topic_scores=topic_scores,
            prerequisite_edges=prerequisite_edges,
            learning_profile=learning_profile,
            goal=goal,
            feature_flags={"ml_recommendation_enabled": False},
        )
