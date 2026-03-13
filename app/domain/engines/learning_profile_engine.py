from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True)
class LearningProfileResult:
    profile_type: str
    confidence: float


class LearningProfileEngine:
    """
    Builds a lightweight learning profile from diagnostic behavior.

    Inputs:
    - response_times: per-question time in seconds
    - accuracies: per-question score in percentage (0-100)
    - difficulty_distribution: counts per difficulty label
      expected keys: easy, medium, hard
    """

    PROFILE_CONCEPT_FOCUSED = "concept_focused"
    PROFILE_PRACTICE_FOCUSED = "practice_focused"
    PROFILE_BALANCED = "balanced"
    PROFILE_SLOW_DEEP = "slow_deep_learner"

    def analyze(
        self,
        response_times: list[float],
        accuracies: list[float],
        difficulty_distribution: dict[str, int],
    ) -> LearningProfileResult:
        if not response_times or not accuracies:
            return LearningProfileResult(profile_type=self.PROFILE_BALANCED, confidence=0.5)

        avg_time = mean(response_times)
        avg_accuracy = mean(accuracies)

        easy = int(difficulty_distribution.get("easy", 0))
        medium = int(difficulty_distribution.get("medium", 0))
        hard = int(difficulty_distribution.get("hard", 0))
        total_difficulty = max(easy + medium + hard, 1)

        hard_ratio = hard / total_difficulty
        easy_ratio = easy / total_difficulty

        # Deterministic profile scoring.
        concept_score = 0.0
        practice_score = 0.0
        slow_deep_score = 0.0

        if avg_accuracy >= 75:
            concept_score += 0.45
        if hard_ratio >= 0.35:
            concept_score += 0.35
        if 12 <= avg_time <= 35:
            concept_score += 0.2

        if avg_accuracy < 65:
            practice_score += 0.45
        if easy_ratio >= 0.45:
            practice_score += 0.3
        if avg_time < 18:
            practice_score += 0.25

        if avg_time > 40:
            slow_deep_score += 0.5
        if avg_accuracy >= 70:
            slow_deep_score += 0.3
        if hard_ratio >= 0.25:
            slow_deep_score += 0.2

        scores = {
            self.PROFILE_CONCEPT_FOCUSED: concept_score,
            self.PROFILE_PRACTICE_FOCUSED: practice_score,
            self.PROFILE_SLOW_DEEP: slow_deep_score,
            self.PROFILE_BALANCED: 0.6,
        }

        top_profile = max(scores, key=scores.get)
        sorted_scores = sorted(scores.values(), reverse=True)
        margin = sorted_scores[0] - sorted_scores[1]

        confidence = min(0.99, max(0.5, scores[top_profile] + margin / 2))
        return LearningProfileResult(profile_type=top_profile, confidence=round(confidence, 2))
