from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class LearningResource:
    topic_id: int
    resource_type: str
    title: str
    priority: int
    reason: str


class ContentRecommendationEngine:
    RESOURCE_TYPES: Final[tuple[str, ...]] = (
        "course",
        "video",
        "project",
        "documentation",
    )

    _PROFILE_RESOURCE_ORDER: Final[dict[str, tuple[str, ...]]] = {
        "concept_focused": ("documentation", "course", "video", "project"),
        "practice_focused": ("project", "video", "course", "documentation"),
        "slow_deep_learner": ("course", "documentation", "video", "project"),
        "balanced": ("course", "video", "project", "documentation"),
    }

    def recommend_resources(
        self,
        user_learning_profile: dict,
        topic_scores: dict[int, float],
        goal: dict,
        resources_per_topic: int = 2,
    ) -> list[LearningResource]:
        """
        Return deterministic, weak-topic-prioritized resources.

        Rules:
        - weaker score => higher priority
        - profile affects resource-type ordering
        - mastered topics (>70) are only included if no weak topics exist
        """
        if not topic_scores:
            return []

        profile_type = str(user_learning_profile.get("profile_type", "balanced"))
        profile_order = self._PROFILE_RESOURCE_ORDER.get(
            profile_type,
            self._PROFILE_RESOURCE_ORDER["balanced"],
        )

        weak_topics = sorted(
            (topic_id for topic_id, score in topic_scores.items() if score <= 70.0),
            key=lambda topic_id: (topic_scores[topic_id], topic_id),
        )
        candidate_topics = weak_topics
        if not candidate_topics:
            candidate_topics = sorted(topic_scores.keys(), key=lambda topic_id: (topic_scores[topic_id], topic_id))

        goal_name = str(goal.get("name", "Learning Goal"))
        recommendations: list[LearningResource] = []
        priority = 1

        for topic_id in candidate_topics:
            score = float(topic_scores[topic_id])
            level = self._mastery_level(score)
            selected_types = profile_order[: max(1, min(resources_per_topic, len(profile_order)))]

            for resource_type in selected_types:
                recommendations.append(
                    LearningResource(
                        topic_id=topic_id,
                        resource_type=resource_type,
                        title=f"{goal_name}: Topic {topic_id} {resource_type.title()}",
                        priority=priority,
                        reason=f"Topic {topic_id} is {level} (score={score:.1f}); prioritized for improvement.",
                    )
                )
                priority += 1

        return recommendations

    @staticmethod
    def _mastery_level(score: float) -> str:
        if score < 50:
            return "beginner"
        if score <= 70:
            return "needs_practice"
        return "mastered"
