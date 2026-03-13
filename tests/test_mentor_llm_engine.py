from app.domain.engines.mentor_llm_engine import MentorContext, RuleBasedMentorLLMEngine


def test_generate_response_includes_context_signals():
    engine = RuleBasedMentorLLMEngine()
    context = MentorContext(
        user_roadmap={"total_steps": 12, "completion_rate": 40.0},
        weak_topics=[3, 1],
        learning_profile={"profile_type": "practice_focused"},
    )

    response = engine.generate_response(context=context, message="How should I improve this week?")
    assert "practice_focused" in response
    assert "12 steps" in response
    assert "40.0%" in response
    assert "1, 3" in response


def test_generate_response_empty_message_guard():
    engine = RuleBasedMentorLLMEngine()
    context = MentorContext(user_roadmap={}, weak_topics=[], learning_profile={})
    response = engine.generate_response(context=context, message="   ")
    assert "Please share your learning question" in response
