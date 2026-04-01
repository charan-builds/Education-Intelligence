from app.domain.engines.adaptive_testing_engine import AdaptiveQuestion, AdaptiveTestingEngine


def _questions():
    return [
        AdaptiveQuestion(id=1, topic_id=10, difficulty=1, question_type="multiple_choice", question_text="q1"),
        AdaptiveQuestion(id=2, topic_id=10, difficulty=2, question_type="multiple_choice", question_text="q2"),
        AdaptiveQuestion(id=3, topic_id=10, difficulty=3, question_type="multiple_choice", question_text="q3"),
        AdaptiveQuestion(id=7, topic_id=10, difficulty=3, question_type="multiple_choice", question_text="q7"),
        AdaptiveQuestion(id=4, topic_id=20, difficulty=1, question_type="multiple_choice", question_text="q4"),
        AdaptiveQuestion(id=5, topic_id=20, difficulty=2, question_type="multiple_choice", question_text="q5"),
        AdaptiveQuestion(id=6, topic_id=20, difficulty=3, question_type="multiple_choice", question_text="q6"),
    ]


def test_two_correct_answers_increase_difficulty():
    engine = AdaptiveTestingEngine()
    previous_answers = [
        {"question_id": 2, "score": 90.0},
        {"question_id": 3, "score": 95.0},
    ]
    next_question = engine.select_next_question(_questions(), previous_answers, {10: 40.0, 20: 80.0})
    assert next_question is not None
    assert next_question.difficulty == 3


def test_two_failed_answers_decrease_difficulty():
    engine = AdaptiveTestingEngine()
    previous_answers = [
        {"question_id": 3, "score": 20.0},
        {"question_id": 2, "score": 10.0},
    ]
    next_question = engine.select_next_question(_questions(), previous_answers, {10: 30.0, 20: 80.0})
    assert next_question is not None
    assert next_question.difficulty == 1


def test_knowledge_gap_topic_priority():
    engine = AdaptiveTestingEngine()
    next_question = engine.select_next_question(_questions(), [], {10: 88.0, 20: 25.0})
    assert next_question is not None
    assert next_question.topic_id == 20


def test_selection_is_deterministic():
    engine = AdaptiveTestingEngine()
    previous_answers = [{"question_id": 1, "score": 75.0}]
    topic_scores = {10: 60.0, 20: 60.0}
    q1 = engine.select_next_question(_questions(), previous_answers, topic_scores)
    q2 = engine.select_next_question(_questions(), previous_answers, topic_scores)
    assert q1 is not None and q2 is not None
    assert q1.id == q2.id


def test_selection_stops_after_max_questions():
    engine = AdaptiveTestingEngine()
    previous_answers = [{"question_id": index + 1, "score": 80.0} for index in range(engine.MAX_QUESTIONS)]
    assert engine.select_next_question(_questions(), previous_answers, {10: 50.0, 20: 50.0}) is None
