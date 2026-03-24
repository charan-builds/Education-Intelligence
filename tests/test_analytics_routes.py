import asyncio
from types import SimpleNamespace

from app.presentation.analytics_routes import (
    get_analytics_overview,
    get_platform_analytics_overview,
    get_roadmap_progress_analytics,
    get_topic_mastery_analytics,
)


class StubAnalyticsService:
    def __init__(self, _db):
        self.db = _db

    async def aggregated_metrics(self, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "topic_mastery_distribution": {"beginner": 1, "needs_practice": 2, "mastered": 3},
            "diagnostic_completion_rate": 75.0,
            "roadmap_completion_rate": 42.0,
        }

    async def roadmap_progress_summary(self, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "student_count": 1,
            "average_completion_percent": 50,
            "average_mastery_percent": 70,
            "learners": [
                {
                    "user_id": 10,
                    "email": "student@example.com",
                    "total_steps": 4,
                    "completed_steps": 2,
                    "in_progress_steps": 1,
                    "pending_steps": 1,
                    "completion_percent": 50,
                    "mastery_percent": 70,
                }
            ],
        }

    async def topic_mastery_summary(self, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "topic_mastery_distribution": {"beginner": 4, "needs_practice": 5, "mastered": 6},
        }

    async def platform_overview(self):
        return {
            "tenant_count": 3,
            "student_count": 12,
            "mentor_count": 2,
            "teacher_count": 4,
            "admin_count": 3,
            "super_admin_count": 1,
            "diagnostic_completion_rate": 77.5,
            "roadmap_completion_rate": 48.5,
            "average_completion_percent": 52,
            "average_mastery_percent": 67,
            "topic_mastery_distribution": {"beginner": 4, "needs_practice": 5, "mastered": 6},
            "tenant_breakdown": [
                {
                    "tenant_id": 9,
                    "tenant_name": "Acme",
                    "tenant_type": "school",
                    "student_count": 8,
                    "mentor_count": 1,
                    "teacher_count": 2,
                    "admin_count": 1,
                    "super_admin_count": 0,
                    "diagnostic_completion_rate": 80.0,
                    "roadmap_completion_rate": 50.0,
                    "average_completion_percent": 55,
                    "average_mastery_percent": 70,
                }
            ],
        }


def test_get_analytics_overview(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.AnalyticsService", StubAnalyticsService)
    current_user = SimpleNamespace(tenant_id=9)

    response = asyncio.run(get_analytics_overview(db=object(), current_user=current_user))

    assert response["tenant_id"] == 9
    assert response["topic_mastery_distribution"]["mastered"] == 3


def test_get_roadmap_progress_analytics(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.AnalyticsService", StubAnalyticsService)
    current_user = SimpleNamespace(tenant_id=4)

    response = asyncio.run(get_roadmap_progress_analytics(db=object(), current_user=current_user))

    assert response["tenant_id"] == 4
    assert response["student_count"] == 1
    assert response["learners"][0]["completion_percent"] == 50


def test_get_topic_mastery_analytics(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.AnalyticsService", StubAnalyticsService)
    current_user = SimpleNamespace(tenant_id=7)

    response = asyncio.run(get_topic_mastery_analytics(db=object(), current_user=current_user))

    assert response["tenant_id"] == 7
    assert response["topic_mastery_distribution"]["mastered"] == 6


def test_get_platform_analytics_overview(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.AnalyticsService", StubAnalyticsService)

    response = asyncio.run(get_platform_analytics_overview(db=object(), _current_user=SimpleNamespace(role="super_admin")))

    assert response["tenant_count"] == 3
    assert response["student_count"] == 12
    assert response["tenant_breakdown"][0]["tenant_name"] == "Acme"
