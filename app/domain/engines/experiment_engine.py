from __future__ import annotations

import hashlib
from typing import Final


class ExperimentEngine:
    """
    Deterministic experiment assignment engine.

    Uses a stable hash of (experiment_name, user_id) to assign one of:
    control, variant_a, variant_b.
    """

    SUPPORTED_EXPERIMENTS: Final[tuple[str, ...]] = (
        "recommendation_algorithm",
        "diagnostic_question_strategy",
        "roadmap_generation_strategy",
    )
    VARIANTS: Final[tuple[str, ...]] = ("control", "variant_a", "variant_b")

    def __init__(self) -> None:
        # Optional memoization to avoid recomputing in a process lifetime.
        self._assignments: dict[tuple[int, str], str] = {}

    def assign_user_to_experiment(self, user_id: int, experiment_name: str) -> str:
        self._validate_experiment(experiment_name)
        cache_key = (user_id, experiment_name)
        if cache_key in self._assignments:
            return self._assignments[cache_key]

        variant = self._compute_variant(user_id=user_id, experiment_name=experiment_name)
        self._assignments[cache_key] = variant
        return variant

    def get_experiment_variant(self, user_id: int, experiment_name: str) -> str:
        self._validate_experiment(experiment_name)
        cache_key = (user_id, experiment_name)
        if cache_key in self._assignments:
            return self._assignments[cache_key]
        return self.assign_user_to_experiment(user_id=user_id, experiment_name=experiment_name)

    def _compute_variant(self, user_id: int, experiment_name: str) -> str:
        seed = f"{experiment_name}:{user_id}".encode("utf-8")
        digest = hashlib.sha256(seed).hexdigest()
        bucket = int(digest[:8], 16) % len(self.VARIANTS)
        return self.VARIANTS[bucket]

    def _validate_experiment(self, experiment_name: str) -> None:
        if experiment_name not in self.SUPPORTED_EXPERIMENTS:
            raise ValueError(f"Unsupported experiment: {experiment_name}")
