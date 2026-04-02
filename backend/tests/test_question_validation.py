import pytest

from app.domain.models.question import Question, validate_question_configuration


def test_multiple_choice_requires_answer_options():
    question = Question(
        topic_id=1,
        difficulty=1,
        question_type="multiple_choice",
        question_text="What is 2 + 2?",
        correct_answer="4",
        accepted_answers=[],
        answer_options=[],
    )

    with pytest.raises(ValueError, match="require non-empty answer_options"):
        validate_question_configuration(question)


def test_short_text_disallows_answer_options():
    question = Question(
        topic_id=1,
        difficulty=1,
        question_type="short_text",
        question_text="Define a vector.",
        correct_answer="quantity with magnitude and direction",
        accepted_answers=[],
        answer_options=["A", "B"],
    )

    with pytest.raises(ValueError, match="must not define answer_options"):
        validate_question_configuration(question)


def test_supported_question_type_configuration_passes():
    question = Question(
        topic_id=1,
        difficulty=1,
        question_type="multiple_choice",
        question_text="What is 2 + 2?",
        correct_answer="4",
        accepted_answers=["four"],
        answer_options=["3", "4", "5"],
    )

    validate_question_configuration(question)
