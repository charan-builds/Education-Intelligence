from app.domain.engines.prerequisite_tracer import PrerequisiteTracer
from app.domain.engines.recommendation_engine import RecommendationEngine


class RuleEngine(RecommendationEngine):
    def classify_topic(self, score: float) -> str:
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
        classifications = {topic_id: self.classify_topic(score) for topic_id, score in topic_scores.items()}
        weak_topics = [topic_id for topic_id, level in classifications.items() if level != "mastered"]

        tracer = PrerequisiteTracer(prerequisite_edges)
        ordered: list[int] = []
        seen: set[int] = set()
        for topic_id in weak_topics:
            foundations = tracer.trace_all(topic_id)
            for node in foundations + [topic_id]:
                if node not in seen:
                    ordered.append(node)
                    seen.add(node)
        return ordered
