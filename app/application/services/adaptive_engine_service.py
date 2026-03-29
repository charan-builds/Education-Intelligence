from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AdaptiveDecision:
    topic_id: int
    current_difficulty: int
    recommended_difficulty: int
    accuracy: float
    time_taken: float
    attempt_count: int
    level: str
    rule: str


@dataclass(frozen=True)
class AdaptiveTopicProfile:
    topic_id: int
    level: str
    average_accuracy: float
    average_time_taken: float
    average_attempts: float
    recommended_difficulty: int


class AdaptiveEngineService:
    FAST_THRESHOLD_SECONDS = 20.0
    SLOW_THRESHOLD_SECONDS = 45.0
    HIGH_ACCURACY_THRESHOLD = 0.85
    LOW_ACCURACY_THRESHOLD = 0.5
    MAX_DIFFICULTY = 3
    MIN_DIFFICULTY = 1

    @staticmethod
    def _clamp_difficulty(value: int) -> int:
        return max(AdaptiveEngineService.MIN_DIFFICULTY, min(AdaptiveEngineService.MAX_DIFFICULTY, int(value)))

    @staticmethod
    def _classify_level(*, average_accuracy: float, average_time_taken: float, average_attempts: float) -> str:
        if average_accuracy >= 0.85 and average_time_taken <= 25.0 and average_attempts <= 1.2:
            return "advanced"
        if average_accuracy >= 0.6 and average_attempts <= 2.0:
            return "intermediate"
        return "beginner"

    def evaluate_answer(
        self,
        *,
        topic_id: int,
        current_difficulty: int,
        score: float,
        time_taken: float,
        attempt_count: int,
    ) -> AdaptiveDecision:
        accuracy = round(max(0.0, min(1.0, float(score) / 100.0)), 4)
        recommended_difficulty = self._clamp_difficulty(current_difficulty)
        rule = "maintain_difficulty"

        fast_and_accurate = (
            accuracy >= self.HIGH_ACCURACY_THRESHOLD
            and float(time_taken) <= self.FAST_THRESHOLD_SECONDS
            and int(attempt_count) <= 1
        )
        slow_and_incorrect = (
            accuracy < self.LOW_ACCURACY_THRESHOLD
            and (float(time_taken) >= self.SLOW_THRESHOLD_SECONDS or int(attempt_count) >= 2)
        )

        if fast_and_accurate:
            recommended_difficulty = self._clamp_difficulty(current_difficulty + 1)
            rule = "increase_difficulty"
        elif slow_and_incorrect:
            recommended_difficulty = self._clamp_difficulty(current_difficulty - 1)
            rule = "reduce_difficulty"
        elif accuracy >= 0.7 and int(attempt_count) <= 2:
            rule = "reinforce_current_band"
        elif int(attempt_count) >= 3:
            recommended_difficulty = self._clamp_difficulty(current_difficulty - 1)
            rule = "reduce_after_multiple_attempts"

        level = self._classify_level(
            average_accuracy=accuracy,
            average_time_taken=float(time_taken),
            average_attempts=float(attempt_count),
        )
        return AdaptiveDecision(
            topic_id=int(topic_id),
            current_difficulty=int(current_difficulty),
            recommended_difficulty=recommended_difficulty,
            accuracy=accuracy,
            time_taken=round(float(time_taken), 2),
            attempt_count=int(attempt_count),
            level=level,
            rule=rule,
        )

    def classify_topic_levels(self, rows: list[dict]) -> list[AdaptiveTopicProfile]:
        grouped: dict[int, list[dict]] = defaultdict(list)
        for row in rows:
            grouped[int(row["topic_id"])].append(row)

        profiles: list[AdaptiveTopicProfile] = []
        for topic_id, topic_rows in sorted(grouped.items()):
            average_accuracy = round(
                sum(float(row.get("accuracy", 0.0) or 0.0) for row in topic_rows) / max(len(topic_rows), 1),
                4,
            )
            average_time_taken = round(
                sum(float(row.get("time_taken", 0.0) or 0.0) for row in topic_rows) / max(len(topic_rows), 1),
                2,
            )
            average_attempts = round(
                sum(float(row.get("attempt_count", 1) or 1) for row in topic_rows) / max(len(topic_rows), 1),
                2,
            )
            average_difficulty = round(
                sum(int(row.get("difficulty", 2) or 2) for row in topic_rows) / max(len(topic_rows), 1)
            )
            level = self._classify_level(
                average_accuracy=average_accuracy,
                average_time_taken=average_time_taken,
                average_attempts=average_attempts,
            )
            recommended_difficulty = self._clamp_difficulty(average_difficulty)
            if level == "advanced":
                recommended_difficulty = self._clamp_difficulty(recommended_difficulty + 1)
            elif level == "beginner":
                recommended_difficulty = self._clamp_difficulty(recommended_difficulty - 1)
            profiles.append(
                AdaptiveTopicProfile(
                    topic_id=topic_id,
                    level=level,
                    average_accuracy=average_accuracy,
                    average_time_taken=average_time_taken,
                    average_attempts=average_attempts,
                    recommended_difficulty=recommended_difficulty,
                )
            )
        return profiles

    def serialize_decision(self, decision: AdaptiveDecision) -> dict:
        return asdict(decision)

    def serialize_topic_profiles(self, profiles: list[AdaptiveTopicProfile]) -> list[dict]:
        return [asdict(profile) for profile in profiles]
