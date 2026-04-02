from app.domain.engines.job_readiness_engine import JobReadinessEngine


def test_job_readiness_weighted_score_with_completion_rate():
    engine = JobReadinessEngine()
    result = engine.compute_score(
        user_skills=[
            {"skill_id": 1, "average_score": 80.0},
            {"skill_id": 2, "average_score": 60.0},
        ],
        completed_roadmap={"completion_rate": 50.0},
        topic_mastery={10: 70.0, 20: 90.0},
    )

    # skill=70, topic=80, practice=50 => 70*0.4 + 80*0.35 + 50*0.25 = 68.5
    assert result["job_readiness_score"] == 68.5


def test_job_readiness_uses_step_ratio_when_completion_rate_missing():
    engine = JobReadinessEngine()
    result = engine.compute_score(
        user_skills=[{"average_score": 100.0}],
        completed_roadmap={"completed_steps": 3, "total_steps": 4},
        topic_mastery={1: 100.0},
    )

    # practice=75
    assert result["breakdown"]["practice_completion"] == 75.0


def test_job_readiness_clamps_out_of_range_values():
    engine = JobReadinessEngine()
    result = engine.compute_score(
        user_skills=[{"average_score": 200.0}, {"average_score": -20.0}],
        completed_roadmap={"completion_rate": 200.0},
        topic_mastery={1: -10.0, 2: 120.0},
    )

    assert 0.0 <= result["job_readiness_score"] <= 100.0
    assert result["breakdown"]["practice_completion"] == 100.0


def test_job_readiness_empty_inputs_returns_zeroes():
    engine = JobReadinessEngine()
    result = engine.compute_score(user_skills=[], completed_roadmap={}, topic_mastery={})

    assert result["job_readiness_score"] == 0.0
    assert result["breakdown"] == {
        "skill_coverage": 0.0,
        "topic_mastery": 0.0,
        "practice_completion": 0.0,
    }
