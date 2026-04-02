from abc import ABC, abstractmethod


class RecommendationEngine(ABC):
    @abstractmethod
    def classify_topic(self, score: float) -> str:
        raise NotImplementedError

    @abstractmethod
    def recommend_roadmap_steps(
        self,
        topic_scores: dict[int, float],
        prerequisite_edges: list[tuple[int, int]],
        learning_profile: dict | None = None,
        goal: dict | None = None,
    ) -> list[int]:
        raise NotImplementedError
