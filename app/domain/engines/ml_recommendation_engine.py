from app.domain.engines.recommendation_engine import RecommendationEngine


class MLRecommendationEngine(RecommendationEngine):
    """
    Placeholder ML engine.
    In production, this class can call a model server or load a local model.
    """

    def classify_topic(self, score: float) -> str:
        # Keep classification thresholds compatible with rule engine for MVP stability.
        if score < 50:
            return "beginner"
        if score <= 70:
            return "needs_practice"
        return "mastered"

    def recommend_roadmap_steps(
        self,
        topic_scores: dict[int, float],
        prerequisite_edges: list[tuple[int, int]],
        learning_profile: dict | None = None,
        goal: dict | None = None,
    ) -> list[int]:
        data = {
            "topic_scores": topic_scores,
            "learning_profile": learning_profile or {},
            "goal": goal or {},
            "prerequisite_edges": prerequisite_edges,
        }
        return self.predict_recommendations(data)

    def predict_recommendations(self, data: dict) -> list[int]:
        """
        Placeholder model interface.
        A trained model implementation will replace this later.
        """
        topic_scores: dict[int, float] = data.get("topic_scores", {})
        learning_profile: dict = data.get("learning_profile", {})

        # Deterministic fallback heuristic for pre-ML phase.
        sorted_topics = sorted(topic_scores.items(), key=lambda kv: kv[1])
        profile_type = learning_profile.get("profile_type", "balanced")

        if profile_type == "slow_deep_learner":
            threshold = 80
        elif profile_type == "practice_focused":
            threshold = 75
        else:
            threshold = 70

        return [topic_id for topic_id, score in sorted_topics if score <= threshold]
