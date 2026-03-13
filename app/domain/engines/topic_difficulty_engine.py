from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TopicDifficultyResult:
    score: float
    level: str


class TopicDifficultyEngine:
    """
    difficulty = 0.5 * failure_rate + 0.3 * time_factor + 0.2 * score_factor

    Inputs are expected to be normalized to [0, 1].
    """

    def compute_score(self, failure_rate: float, time_factor: float, score_factor: float) -> float:
        score = (0.5 * failure_rate) + (0.3 * time_factor) + (0.2 * score_factor)
        return round(max(0.0, min(1.0, score)), 4)

    @staticmethod
    def classify(score: float) -> str:
        if score < 0.25:
            return "easy"
        if score < 0.5:
            return "medium"
        if score < 0.75:
            return "hard"
        return "expert"

    def evaluate(self, failure_rate: float, time_factor: float, score_factor: float) -> TopicDifficultyResult:
        score = self.compute_score(
            failure_rate=failure_rate,
            time_factor=time_factor,
            score_factor=score_factor,
        )
        return TopicDifficultyResult(score=score, level=self.classify(score))
