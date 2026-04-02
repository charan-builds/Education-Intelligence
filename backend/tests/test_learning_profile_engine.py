from app.domain.engines.learning_profile_engine import LearningProfileEngine


def test_detects_concept_focused_profile():
    engine = LearningProfileEngine()
    result = engine.analyze(
        response_times=[18, 20, 22, 16],
        accuracies=[82, 88, 79, 91],
        difficulty_distribution={"easy": 1, "medium": 2, "hard": 3},
    )
    assert result.profile_type == "concept_focused"
    assert 0.5 <= result.confidence <= 0.99


def test_detects_practice_focused_profile():
    engine = LearningProfileEngine()
    result = engine.analyze(
        response_times=[10, 12, 14, 9],
        accuracies=[45, 52, 60, 55],
        difficulty_distribution={"easy": 4, "medium": 1, "hard": 0},
    )
    assert result.profile_type == "practice_focused"


def test_detects_slow_deep_learner_profile():
    engine = LearningProfileEngine()
    result = engine.analyze(
        response_times=[45, 52, 49, 57],
        accuracies=[72, 76, 80, 74],
        difficulty_distribution={"easy": 1, "medium": 2, "hard": 2},
    )
    assert result.profile_type == "slow_deep_learner"


def test_defaults_to_balanced_with_sparse_input():
    engine = LearningProfileEngine()
    result = engine.analyze(response_times=[], accuracies=[], difficulty_distribution={})
    assert result.profile_type == "balanced"
    assert result.confidence == 0.5
