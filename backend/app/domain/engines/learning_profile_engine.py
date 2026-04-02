from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev


@dataclass(frozen=True)
class LearningProfileResult:
    profile_type: str
    confidence: float
    speed: float
    accuracy: float
    consistency: float
    stamina: float


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
    PROFILE_FAST_EXPLORER = "fast_explorer"

    def analyze(
        self,
        response_times: list[float],
        accuracies: list[float],
        difficulty_distribution: dict[str, int],
    ) -> LearningProfileResult:
        if not response_times or not accuracies:
            return LearningProfileResult(
                profile_type=self.PROFILE_BALANCED,
                confidence=0.5,
                speed=50.0,
                accuracy=50.0,
                consistency=50.0,
                stamina=50.0,
            )

        avg_time = mean(response_times)
        avg_accuracy = mean(accuracies)
        time_variance = pstdev(response_times) if len(response_times) > 1 else 0.0
        accuracy_variance = pstdev(accuracies) if len(accuracies) > 1 else 0.0

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
        fast_explorer_score = 0.0

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

        if avg_time < 16:
            fast_explorer_score += 0.45
        if avg_accuracy >= 62:
            fast_explorer_score += 0.25
        if hard_ratio >= 0.2:
            fast_explorer_score += 0.15
        if time_variance < 10:
            fast_explorer_score += 0.15

        scores = {
            self.PROFILE_CONCEPT_FOCUSED: concept_score,
            self.PROFILE_PRACTICE_FOCUSED: practice_score,
            self.PROFILE_SLOW_DEEP: slow_deep_score,
            self.PROFILE_FAST_EXPLORER: fast_explorer_score,
            self.PROFILE_BALANCED: 0.6,
        }

        top_profile = max(scores, key=scores.get)
        sorted_scores = sorted(scores.values(), reverse=True)
        margin = sorted_scores[0] - sorted_scores[1]

        confidence = min(0.99, max(0.5, scores[top_profile] + margin / 2))
        speed = max(0.0, min(100.0, 100.0 - min(avg_time, 90.0) / 90.0 * 100.0))
        consistency = max(
            0.0,
            min(100.0, 100.0 - ((time_variance * 1.3) + (accuracy_variance * 0.35))),
        )
        stamina = max(0.0, min(100.0, (hard_ratio * 65.0) + (avg_accuracy * 0.35)))
        return LearningProfileResult(
            profile_type=top_profile,
            confidence=round(confidence, 2),
            speed=round(speed, 2),
            accuracy=round(avg_accuracy, 2),
            consistency=round(consistency, 2),
            stamina=round(stamina, 2),
        )
