from datetime import date

import pytest

from app.domain.engines.learning_simulation_engine import LearningSimulationEngine


def test_simulation_outputs_completion_date_and_curve():
    engine = LearningSimulationEngine()
    roadmap = {
        "start_date": date(2026, 1, 1),
        "steps": [
            {"topic_id": 1, "estimated_time_hours": 10},
            {"topic_id": 2, "estimated_time_hours": 5},
        ],
    }

    result = engine.simulate(roadmap=roadmap, daily_study_hours=3)

    assert result.estimated_completion_date.isoformat() == "2026-01-06"
    assert result.progress_curve[-1]["progress_percent"] == 100.0
    assert len(result.progress_curve) == 5


def test_simulation_rejects_non_positive_study_hours():
    engine = LearningSimulationEngine()
    with pytest.raises(ValueError):
        engine.simulate(roadmap={"steps": []}, daily_study_hours=0)
