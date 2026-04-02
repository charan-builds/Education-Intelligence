from app.domain.engines.topic_difficulty_engine import TopicDifficultyEngine


def test_weighted_difficulty_formula():
    engine = TopicDifficultyEngine()
    # 0.5*0.8 + 0.3*0.5 + 0.2*0.7 = 0.69
    result = engine.evaluate(failure_rate=0.8, time_factor=0.5, score_factor=0.7)
    assert result.score == 0.69
    assert result.level == "hard"


def test_level_bands():
    engine = TopicDifficultyEngine()
    assert engine.classify(0.1) == "easy"
    assert engine.classify(0.3) == "medium"
    assert engine.classify(0.6) == "hard"
    assert engine.classify(0.9) == "expert"
