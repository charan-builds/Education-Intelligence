import asyncio
from types import SimpleNamespace

from app.presentation.analytics_routes import (
    get_analytics_overview,
    get_learning_trends,
    get_platform_analytics_overview,
    get_roadmap_progress_analytics,
    get_skill_vectors,
    get_student_insights,
    get_topic_mastery_analytics,
    get_weak_topics,
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

    async def roadmap_progress_summary(self, tenant_id: int, *, limit: int = 20, offset: int = 0):
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
            "meta": {
                "total": 1,
                "limit": limit,
                "offset": offset,
                "next_offset": None,
                "next_cursor": None,
            },
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

    response = asyncio.run(
        get_roadmap_progress_analytics(
            db=object(),
            current_user=current_user,
            pagination=SimpleNamespace(limit=20, offset=0),
        )
    )

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


class StubSkillVectorService:
    def __init__(self, _db):
        self.db = _db

    async def aggregated_feature_payload(self, *, tenant_id: int, user_id: int):
        return {
            "mastery_avg": 62.0,
            "confidence_avg": 0.71,
            "learning_speed_seconds": 38.0,
            "retry_count": 2,
            "tracked_topics": 5,
        }

    async def learner_vectors(self, *, tenant_id: int, user_id: int):
        return [
            {
                "topic_id": 4,
                "topic_name": "SQL",
                "mastery_score": 61.5,
                "confidence_score": 0.73,
                "last_updated": "2026-03-25T00:00:00Z",
            }
        ]

    async def weak_topics(self, *, tenant_id: int, user_id: int | None = None, limit: int = 8):
        return [
            {
                "topic_id": 4,
                "topic_name": "SQL",
                "mastery_score": 32.0,
                "confidence_score": 0.41,
            }
        ]

    async def learning_trends(self, *, tenant_id: int, days: int = 14):
        return [
            {
                "label": "2026-03-24",
                "events": 12,
                "minutes_spent": 48.0,
                "completions": 4,
                "retries": 2,
            }
        ]


def test_student_intelligence_endpoints(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.SkillVectorService", StubSkillVectorService)
    current_user = SimpleNamespace(tenant_id=7, id=11)

    insights = asyncio.run(get_student_insights(db=object(), current_user=current_user))
    assert insights["mastery_avg"] == 62.0

    vectors = asyncio.run(get_skill_vectors(db=object(), current_user=current_user))
    assert vectors["vectors"][0]["topic_name"] == "SQL"


def test_teacher_intelligence_endpoints(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.SkillVectorService", StubSkillVectorService)
    current_user = SimpleNamespace(tenant_id=7)

    weak_topics = asyncio.run(get_weak_topics(db=object(), current_user=current_user))
    assert weak_topics[0]["mastery_score"] == 32.0

    trends = asyncio.run(get_learning_trends(db=object(), current_user=current_user))
    assert trends[0]["events"] == 12
