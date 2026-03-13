import pytest

from app.domain.engines.experiment_engine import ExperimentEngine


def test_assign_user_to_experiment_is_deterministic():
    engine = ExperimentEngine()
    first = engine.assign_user_to_experiment(101, "recommendation_algorithm")
    second = engine.assign_user_to_experiment(101, "recommendation_algorithm")
    assert first == second


def test_get_experiment_variant_returns_known_variant():
    engine = ExperimentEngine()
    variant = engine.get_experiment_variant(202, "diagnostic_question_strategy")
    assert variant in {"control", "variant_a", "variant_b"}


def test_assignment_is_scoped_per_experiment_name():
    engine = ExperimentEngine()
    v1 = engine.assign_user_to_experiment(303, "recommendation_algorithm")
    v2 = engine.assign_user_to_experiment(303, "roadmap_generation_strategy")
    assert v1 in {"control", "variant_a", "variant_b"}
    assert v2 in {"control", "variant_a", "variant_b"}


def test_unsupported_experiment_raises_value_error():
    engine = ExperimentEngine()
    with pytest.raises(ValueError):
        engine.assign_user_to_experiment(1, "unknown_experiment")
