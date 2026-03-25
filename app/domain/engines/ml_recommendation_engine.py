from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import exp

from app.domain.engines.prerequisite_tracer import PrerequisiteTracer
from app.domain.engines.recommendation_engine import RecommendationEngine


@dataclass(frozen=True)
class RecommendationComponentBreakdown:
    mastery_gap: float
    confidence_gap: float
    recency_decay: float
    difficulty_weight: float
    learning_velocity_penalty: float
    prerequisite_weight: float
    goal_importance: float
    priority_score: float


@dataclass(frozen=True)
class RankedTopicRecommendation:
    topic_id: int
    priority_score: float
    explanation: str
    components: RecommendationComponentBreakdown | None = None


class MLRecommendationEngine(RecommendationEngine):
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
        ranked = self.rank_topics(
            topic_scores=topic_scores,
            prerequisite_edges=prerequisite_edges,
            learning_profile=learning_profile,
            goal=goal,
        )
        threshold = 70.0
        profile_type = str((learning_profile or {}).get("profile_type", "balanced"))
        if profile_type == "slow_deep_learner":
            threshold = 80.0
        elif profile_type == "practice_focused":
            threshold = 75.0
        return [item.topic_id for item in ranked if topic_scores.get(item.topic_id, 100.0) <= threshold]

    def predict_recommendations(self, data: dict) -> list[int]:
        ranked = self.rank_topics(
            topic_scores=data.get("topic_scores", {}),
            prerequisite_edges=data.get("prerequisite_edges", []),
            learning_profile=data.get("learning_profile", {}),
            goal=data.get("goal", {}),
        )
        return [item.topic_id for item in ranked]

    def rank_topics(
        self,
        *,
        topic_scores: dict[int, float],
        prerequisite_edges: list[tuple[int, int]],
        learning_profile: dict | None = None,
        goal: dict | None = None,
    ) -> list[RankedTopicRecommendation]:
        tracer = PrerequisiteTracer(prerequisite_edges)
        profile = learning_profile or {}
        goal_context = goal or {}
        ranked: list[RankedTopicRecommendation] = []
        for topic_id, score in topic_scores.items():
            breakdown = self._score_topic(
                topic_id=int(topic_id),
                mastery=float(score),
                prerequisite_depth=len(tracer.trace_all(int(topic_id))),
                learning_profile=profile,
                goal=goal_context,
            )
            ranked.append(
                RankedTopicRecommendation(
                    topic_id=int(topic_id),
                    priority_score=breakdown.priority_score,
                    explanation=self._explain_topic(topic_id=int(topic_id), components=breakdown),
                    components=breakdown,
                )
            )
        ranked.sort(key=lambda item: (-item.priority_score, item.topic_id))
        return ranked

    def _score_topic(
        self,
        *,
        topic_id: int,
        mastery: float,
        prerequisite_depth: int,
        learning_profile: dict,
        goal: dict,
    ) -> RecommendationComponentBreakdown:
        normalized_mastery = max(0.0, min(100.0, mastery))
        confidence = float(learning_profile.get("confidence_by_topic", {}).get(topic_id, learning_profile.get("confidence", 0.6)))
        confidence = max(0.0, min(1.0, confidence))
        days_since_last_interaction = float(
            learning_profile.get("days_since_last_interaction_by_topic", {}).get(
                topic_id,
                learning_profile.get("days_since_last_interaction", 7),
            )
        )
        difficulty = float(
            learning_profile.get("difficulty_by_topic", {}).get(
                topic_id,
                goal.get("difficulty_by_topic", {}).get(topic_id, 0.5),
            )
        )
        difficulty = max(0.0, min(1.0, difficulty))
        learning_velocity = float(
            learning_profile.get("velocity_by_topic", {}).get(topic_id, learning_profile.get("learning_velocity", 0.5))
        )
        learning_velocity = max(0.0, min(1.0, learning_velocity))
        goal_importance = float(goal.get("importance_by_topic", {}).get(topic_id, goal.get("importance", 0.7)))
        goal_importance = max(0.0, min(1.0, goal_importance))

        mastery_gap = (100.0 - normalized_mastery) / 100.0
        confidence_gap = 1.0 - confidence
        recency_decay = 1.0 - exp(-(days_since_last_interaction / 14.0))
        prerequisite_weight = min(1.0, prerequisite_depth / 5.0)
        learning_velocity_penalty = 1.0 - learning_velocity

        priority_score = round(
            (
                mastery_gap * 0.28
                + confidence_gap * 0.12
                + recency_decay * 0.16
                + difficulty * 0.12
                + learning_velocity_penalty * 0.14
                + prerequisite_weight * 0.08
                + goal_importance * 0.10
            )
            * 100.0,
            2,
        )
        return RecommendationComponentBreakdown(
            mastery_gap=round(mastery_gap, 4),
            confidence_gap=round(confidence_gap, 4),
            recency_decay=round(recency_decay, 4),
            difficulty_weight=round(difficulty, 4),
            learning_velocity_penalty=round(learning_velocity_penalty, 4),
            prerequisite_weight=round(prerequisite_weight, 4),
            goal_importance=round(goal_importance, 4),
            priority_score=priority_score,
        )

    @staticmethod
    def _explain_topic(*, topic_id: int, components: RecommendationComponentBreakdown) -> str:
        drivers: list[str] = []
        if components.mastery_gap >= 0.35:
            drivers.append("low mastery")
        if components.recency_decay >= 0.45:
            drivers.append("long practice gap")
        if components.prerequisite_weight >= 0.4:
            drivers.append("high prerequisite depth")
        if components.goal_importance >= 0.7:
            drivers.append("high goal importance")
        summary = ", ".join(drivers[:3]) if drivers else "balanced factors"
        return f"Topic {topic_id} prioritized because of {summary} as of {datetime.now(timezone.utc).date().isoformat()}."
