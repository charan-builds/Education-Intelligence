from __future__ import annotations

from datetime import datetime, timedelta


def generate_steps(
    *,
    topic_order: list[int],
    topic_scores: dict[int, float],
    dependency_depths: dict[int, int],
    weakness_clusters: list[dict],
    profile_type: str,
    response_times: list[float] | None,
    base_date: datetime,
) -> list[dict]:
    days_per_step = 7
    if profile_type == "slow_deep_learner":
        days_per_step = 10
    elif profile_type == "practice_focused":
        days_per_step = 5

    avg_time = response_times or []
    time_factor = min(1.0, (sum(avg_time) / len(avg_time)) / 60) if avg_time else 0.5

    profile_time_multiplier = 1.0
    if profile_type == "slow_deep_learner":
        profile_time_multiplier = 1.4
    elif profile_type == "practice_focused":
        profile_time_multiplier = 0.85
    elif profile_type == "concept_focused":
        profile_time_multiplier = 1.15

    def _difficulty(score: float) -> str:
        inverse_score = max(0.0, min(1.0, 1 - (score / 100.0)))
        signal = (inverse_score * 0.7) + (time_factor * 0.3)
        if signal >= 0.85:
            return "expert"
        if signal >= 0.6:
            return "hard"
        if signal >= 0.3:
            return "medium"
        return "easy"

    base_hours_by_difficulty = {"easy": 2.0, "medium": 4.0, "hard": 6.0, "expert": 8.0}
    generated_steps: list[dict] = []
    for index, topic_id in enumerate(topic_order):
        difficulty = _difficulty(float(topic_scores.get(topic_id, 50.0)))
        dependency_depth = dependency_depths.get(int(topic_id), 0)
        estimated_time_hours = round(
            base_hours_by_difficulty[difficulty] * profile_time_multiplier * (1 + (dependency_depth * 0.1)),
            2,
        )
        clustered = any(topic_id in cluster.get("topic_ids", []) for cluster in weakness_clusters)
        generated_steps.append(
            {
                "topic_id": int(topic_id),
                "estimated_time_hours": estimated_time_hours,
                "difficulty": difficulty,
                "priority": index + 1,
                "deadline": base_date + timedelta(days=days_per_step * (index + 1)),
                "step_type": "core",
                "rationale": (
                    "Scheduled early to stabilize a weakness cluster and unblock downstream mastery."
                    if clustered
                    else "Scheduled from diagnostic gaps, dependency depth, and learning profile analysis."
                ),
            }
        )
    return generated_steps
