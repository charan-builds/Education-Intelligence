from app.application.services.retention_service import RetentionService


def test_schedule_plan_increases_interval_when_user_performs_well():
    service = RetentionService(session=None)

    schedule = service.schedule_plan(
        score=90.0,
        confidence=0.8,
        days_since_review=1,
        previous_interval_days=4,
        performed_well=True,
    )

    assert schedule["revision_interval_days"] >= 7
    assert schedule["retention_score"] > 0.5


def test_schedule_plan_shortens_interval_when_retention_is_weak():
    service = RetentionService(session=None)

    schedule = service.schedule_plan(
        score=52.0,
        confidence=0.5,
        days_since_review=6,
        previous_interval_days=5,
        performed_well=False,
    )

    assert schedule["revision_interval_days"] <= 3
    assert schedule["retention_score"] < 0.4
