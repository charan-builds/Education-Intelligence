from app.application.services.mentor_service import MentorAdvice, MentorService


def test_rule_based_mentor_generates_personalized_advice():
    service = MentorService()
    result = service.get_personalized_advice(
        diagnostic_results={101: 45.0, 102: 82.0},
        roadmap_progress={"completion_rate": 35.0, "overdue_steps": 2},
        learning_profile={"profile_type": "practice_focused"},
    )

    assert result["risk_level"] in {"medium", "high"}
    assert result["advisor_type"] == "RuleBasedMentorAdvisor"
    assert any("weak topics" in r.lower() for r in result["recommendations"])


def test_service_supports_future_llm_advisor_swap():
    class _FakeLLMAdvisor:
        def generate_advice(self, diagnostic_results, roadmap_progress, learning_profile):
            return MentorAdvice(
                summary="LLM advice",
                recommendations=["Try spaced repetition."],
                risk_level="low",
            )

    service = MentorService(advisor=_FakeLLMAdvisor())
    result = service.get_personalized_advice(
        diagnostic_results={},
        roadmap_progress={"completion_rate": 90.0, "overdue_steps": 0},
        learning_profile={"profile_type": "balanced"},
    )

    assert result["summary"] == "LLM advice"
    assert result["recommendations"] == ["Try spaced repetition."]
    assert result["risk_level"] == "low"
