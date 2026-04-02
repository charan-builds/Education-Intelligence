from datetime import datetime, timedelta, timezone

from app.application.services.mentor_notification_service import MentorNotificationService


def test_mentor_notification_triggers_all_categories():
    service = MentorNotificationService()
    now = datetime(2026, 3, 11, tzinfo=timezone.utc)

    notifications = service.build_notifications(
        roadmap_steps=[
            {
                "topic_id": 10,
                "progress_status": "pending",
                "deadline": now - timedelta(days=1),
            }
        ],
        topic_scores={1: 45.0, 2: 68.0},
        last_activity_at=now - timedelta(days=4),
        now=now,
    )

    triggers = {item.trigger for item in notifications}
    assert MentorNotificationService.TRIGGER_ROADMAP_DEADLINE in triggers
    assert MentorNotificationService.TRIGGER_LEARNING_INACTIVITY in triggers
    assert MentorNotificationService.TRIGGER_TOPIC_WEAKNESS in triggers


def test_mentor_notification_no_inactivity_when_recent_activity():
    service = MentorNotificationService()
    now = datetime(2026, 3, 11, tzinfo=timezone.utc)

    notifications = service.build_notifications(
        roadmap_steps=[],
        topic_scores={1: 88.0},
        last_activity_at=now - timedelta(days=1),
        now=now,
    )

    triggers = {item.trigger for item in notifications}
    assert MentorNotificationService.TRIGGER_LEARNING_INACTIVITY not in triggers
