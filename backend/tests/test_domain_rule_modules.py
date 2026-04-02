from datetime import datetime, timezone

from app.domain.services import diagnostic_rules, roadmap_rules


def test_diagnostic_rules_evaluate_answers_accepts_aliases():
    result = diagnostic_rules.evaluate_answers(
        [{"question_id": 1, "user_answer": "std deviation"}],
        {
            1: type(
                "_Question",
                (),
                {"correct_answer": "standard deviation", "accepted_answers": ["std deviation"]},
            )()
        },
    )

    assert result[0]["score"] == 100.0
    assert result[0]["accuracy"] == 1.0


def test_roadmap_rules_generate_steps_returns_prioritized_steps():
    steps = roadmap_rules.generate_steps(
        topic_order=[101, 202],
        topic_scores={101: 45.0, 202: 75.0},
        dependency_depths={101: 2, 202: 0},
        weakness_clusters=[{"topic_ids": [101]}],
        profile_type="practice_focused",
        response_times=[20.0, 30.0],
        base_date=datetime(2026, 4, 2, tzinfo=timezone.utc),
    )

    assert [step["priority"] for step in steps] == [1, 2]
    assert steps[0]["topic_id"] == 101
    assert steps[0]["step_type"] == "core"
