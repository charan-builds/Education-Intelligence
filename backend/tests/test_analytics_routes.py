import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import HTTPException

from app.presentation.analytics_routes import (
    get_analytics_overview,
    get_learning_trends,
    list_failed_analytics_jobs,
    get_platform_analytics_overview,
    get_precomputed_tenant_dashboard,
    get_precomputed_user_learning_summary,
    get_roadmap_progress_analytics,
    refresh_precomputed_analytics,
    retry_failed_analytics_job,
    get_skill_vectors,
    get_student_performance_analytics,
    get_student_insights,
    get_topic_performance_analytics,
    get_topic_mastery_analytics,
    get_weak_topics,
)


class StubAnalyticsSnapshotService:
    def __init__(self, _db):
        self.db = _db

    async def get_latest_snapshot(self, tenant_id, snapshot_type, *, subject_id=None):
        if snapshot_type == "learner_intelligence_overview":
            return {
                "created_at": None,
                "data": {
                    "tenant_id": tenant_id,
                    "user_id": subject_id,
                    "mastery_avg": 62.0,
                    "confidence_avg": 0.71,
                    "learning_speed_seconds": 38.0,
                    "retry_count": 2,
                    "tracked_topics": 5,
                },
            }
        if snapshot_type == "learning_trends":
            return {
                "created_at": None,
                "data": {
                    "tenant_id": tenant_id,
                    "points": [
                        {
                            "label": "2026-03-24",
                            "events": 12,
                            "minutes_spent": 48.0,
                            "completions": 4,
                            "retries": 2,
                        }
                    ],
                },
            }
        return None


class StubStaleAnalyticsSnapshotService(StubAnalyticsSnapshotService):
    async def get_latest_snapshot(self, tenant_id, snapshot_type, *, subject_id=None):
        snapshot = await super().get_latest_snapshot(tenant_id, snapshot_type, subject_id=subject_id)
        if snapshot is None:
            return None
        snapshot["created_at"] = None
        return snapshot


class StubAnalyticsService:
    def __init__(self, _db):
        self.db = _db

    async def aggregated_metrics(self, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "topic_mastery_distribution": {"beginner": 1, "needs_practice": 2, "mastered": 3},
            "diagnostic_completion_rate": 75.0,
            "roadmap_completion_rate": 42.0,
            "meta": {
                "status": "ready",
                "last_updated": "2026-03-27T00:00:00Z",
                "is_rebuilding": False,
                "estimated_time": None,
            },
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
            "snapshot_meta": {
                "status": "ready",
                "last_updated": "2026-03-27T00:00:00Z",
                "is_rebuilding": False,
                "estimated_time": None,
            },
        }

    async def topic_mastery_summary(self, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "topic_mastery_distribution": {"beginner": 4, "needs_practice": 5, "mastered": 6},
            "meta": {
                "status": "ready",
                "last_updated": "2026-03-27T00:00:00Z",
                "is_rebuilding": False,
                "estimated_time": None,
            },
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
            "meta": {
                "status": "ready",
                "last_updated": "2026-03-27T00:00:00Z",
                "is_rebuilding": False,
                "estimated_time": None,
            },
        }

    async def student_performance_analytics(self, *, tenant_id: int, user_id: int):
        if user_id == 404:
            raise ValueError("Student analytics snapshot not ready")
        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "learning_efficiency_score": 78.4,
            "topic_mastery_heatmap": [
                {
                    "topic_id": 4,
                    "topic_name": "SQL",
                    "mastery_score": 44.0,
                    "average_accuracy": 52.0,
                    "average_time_taken_seconds": 31.5,
                    "average_attempts": 1.7,
                    "last_activity_at": "2026-03-28T00:00:00Z",
                }
            ],
            "weak_topics": [
                {
                    "topic_id": 4,
                    "topic_name": "SQL",
                    "mastery_score": 44.0,
                    "average_accuracy": 52.0,
                    "average_time_taken_seconds": 31.5,
                    "average_attempts": 1.7,
                }
            ],
            "performance_trend": [
                {
                    "label": "2026-03-28",
                    "average_score": 61.0,
                    "average_accuracy": 65.0,
                    "average_time_taken_seconds": 28.0,
                    "answered_questions": 6,
                }
            ],
            "sql_queries": {
                "topic_mastery_heatmap": "select ...",
                "performance_trend": "select ...",
            },
            "meta": {
                "status": "ready",
                "last_updated": "2026-03-27T00:00:00Z",
                "is_rebuilding": False,
                "estimated_time": None,
            },
        }

    async def topic_performance_analytics(self, *, tenant_id: int, topic_id: int):
        if topic_id == 404:
            raise ValueError("Topic analytics snapshot not ready")
        return {
            "tenant_id": tenant_id,
            "topic_id": topic_id,
            "topic_name": "SQL",
            "learner_count": 3,
            "average_mastery_score": 58.0,
            "average_accuracy": 63.0,
            "average_time_taken_seconds": 26.5,
            "learning_efficiency_score": 74.1,
            "weakest_learners": [
                {
                    "user_id": 11,
                    "mastery_score": 41.0,
                    "average_accuracy": 49.0,
                    "average_time_taken_seconds": 34.0,
                    "average_attempts": 1.8,
                }
            ],
            "performance_trend": [
                {
                    "label": "2026-03-28",
                    "learner_count": 3,
                    "average_score": 58.0,
                    "average_accuracy": 63.0,
                    "average_time_taken_seconds": 26.5,
                }
            ],
            "sql_queries": {
                "learner_summary": "select ...",
                "performance_trend": "select ...",
            },
            "meta": {
                "status": "ready",
                "last_updated": "2026-03-27T00:00:00Z",
                "is_rebuilding": False,
                "estimated_time": None,
            },
        }

    def empty_student_performance_analytics(self, *, tenant_id: int, user_id: int):
        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "learning_efficiency_score": 0.0,
            "topic_mastery_heatmap": [],
            "weak_topics": [],
            "performance_trend": [],
            "sql_queries": {},
            "meta": {
                "status": "pending",
                "last_updated": None,
                "is_rebuilding": True,
                "estimated_time": 30,
            },
        }

    async def empty_topic_performance_analytics(self, *, tenant_id: int, topic_id: int):
        return {
            "tenant_id": tenant_id,
            "topic_id": topic_id,
            "topic_name": f"Topic {topic_id}",
            "learner_count": 0,
            "average_mastery_score": 0.0,
            "average_accuracy": 0.0,
            "average_time_taken_seconds": 0.0,
            "learning_efficiency_score": 0.0,
            "weakest_learners": [],
            "performance_trend": [],
            "sql_queries": {},
            "meta": {
                "status": "pending",
                "last_updated": None,
                "is_rebuilding": True,
                "estimated_time": 30,
            },
        }


def test_get_analytics_overview(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.AnalyticsService", StubAnalyticsService)
    current_user = SimpleNamespace(tenant_id=9)

    response = asyncio.run(get_analytics_overview(db=object(), current_user=current_user))

    assert response["tenant_id"] == 9
    assert response["topic_mastery_distribution"]["mastered"] == 3
    assert response["meta"]["status"] == "ready"


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
    assert response["snapshot_meta"]["status"] == "ready"


def test_get_topic_mastery_analytics(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.AnalyticsService", StubAnalyticsService)
    current_user = SimpleNamespace(tenant_id=7)

    response = asyncio.run(get_topic_mastery_analytics(db=object(), current_user=current_user))

    assert response["tenant_id"] == 7
    assert response["topic_mastery_distribution"]["mastered"] == 6
    assert response["meta"]["status"] == "ready"


def test_get_platform_analytics_overview(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.AnalyticsService", StubAnalyticsService)

    response = asyncio.run(get_platform_analytics_overview(db=object(), _current_user=SimpleNamespace(role="super_admin")))

    assert response["tenant_count"] == 3
    assert response["student_count"] == 12
    assert response["tenant_breakdown"][0]["tenant_name"] == "Acme"
    assert response["meta"]["status"] == "ready"


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
    monkeypatch.setattr("app.presentation.analytics_routes.AnalyticsSnapshotService", StubAnalyticsSnapshotService)
    monkeypatch.setattr("app.presentation.analytics_routes.SkillVectorService", StubSkillVectorService)
    current_user = SimpleNamespace(tenant_id=7, id=11)

    insights = asyncio.run(get_student_insights(db=object(), current_user=current_user))
    assert insights["mastery_avg"] == 62.0

    vectors = asyncio.run(get_skill_vectors(db=object(), current_user=current_user))
    assert vectors["vectors"][0]["topic_name"] == "SQL"


def test_student_insights_returns_stale_snapshot_without_blocking(monkeypatch):
    queued = {"called": False}
    monkeypatch.setattr("app.presentation.analytics_routes.AnalyticsSnapshotService", StubAnalyticsSnapshotService)
    monkeypatch.setattr(
        "app.presentation.analytics_routes._snapshot_status",
        lambda last_updated: "stale" if last_updated is None else "ready",
    )
    monkeypatch.setattr(
        "app.presentation.analytics_routes._enqueue_deduplicated_analytics_job",
        lambda **kwargs: queued.update({"called": True, "kwargs": kwargs}) or asyncio.sleep(0, result=True),
    )

    current_user = SimpleNamespace(tenant_id=7, id=11)
    response = asyncio.run(get_student_insights(db=object(), current_user=current_user))

    assert response["mastery_avg"] == 62.0
    assert response["meta"]["status"] == "stale"
    assert queued["called"] is True


def test_teacher_intelligence_endpoints(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.AnalyticsSnapshotService", StubAnalyticsSnapshotService)
    monkeypatch.setattr("app.presentation.analytics_routes.SkillVectorService", StubSkillVectorService)
    current_user = SimpleNamespace(tenant_id=7)

    weak_topics = asyncio.run(get_weak_topics(db=object(), current_user=current_user))
    assert weak_topics[0]["mastery_score"] == 32.0

    trends = asyncio.run(get_learning_trends(db=object(), current_user=current_user))
    assert trends[0]["events"] == 12


def test_precomputed_tenant_dashboard_marks_stale_snapshot(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.PrecomputedAnalyticsService", StubStalePrecomputedAnalyticsService)
    queued = {"called": False}
    monkeypatch.setattr(
        "app.presentation.analytics_routes._enqueue_high_priority_snapshot_rebuild",
        lambda **kwargs: queued.update({"called": True, "kwargs": kwargs}) or asyncio.sleep(0, result=True),
    )
    teacher = SimpleNamespace(tenant_id=9)

    response = asyncio.run(get_precomputed_tenant_dashboard(db=object(), current_user=teacher))

    assert response["tenant_id"] == 9
    assert response["meta"]["status"] == "stale"
    assert queued["called"] is True
    assert queued["kwargs"] == {"tenant_id": 9, "snapshot_type": "tenant_dashboard"}


def test_student_performance_analytics_endpoint(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.AnalyticsService", StubAnalyticsService)
    current_user = SimpleNamespace(tenant_id=7)

    response = asyncio.run(get_student_performance_analytics(user_id=11, db=object(), current_user=current_user))

    assert response["user_id"] == 11
    assert response["learning_efficiency_score"] == 78.4
    assert response["topic_mastery_heatmap"][0]["topic_name"] == "SQL"
    assert response["meta"]["status"] == "ready"


def test_topic_performance_analytics_endpoint(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.AnalyticsService", StubAnalyticsService)
    current_user = SimpleNamespace(tenant_id=7)

    response = asyncio.run(get_topic_performance_analytics(topic_id=4, db=object(), current_user=current_user))

    assert response["topic_id"] == 4
    assert response["topic_name"] == "SQL"
    assert response["weakest_learners"][0]["user_id"] == 11
    assert response["meta"]["status"] == "ready"


def test_student_performance_analytics_queues_when_snapshot_missing(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.AnalyticsService", StubAnalyticsService)
    queued = {}

    class _Cache:
        async def acquire_lock(self, key: str, *, ttl: int):
            queued["lock_key"] = key
            queued["ttl"] = ttl
            return "token-1"

        async def release_lock(self, key: str, token: str | None = None):
            queued["released"] = (key, token)
            return True

    monkeypatch.setattr("app.presentation.analytics_routes.CacheService", lambda: _Cache())
    monkeypatch.setattr(
        "app.presentation.analytics_routes.enqueue_job_with_options",
        lambda task_name, *, args=None, kwargs=None, countdown=None: queued.update(
            {"task_name": task_name, "kwargs": kwargs, "countdown": countdown}
        )
        or True,
    )
    current_user = SimpleNamespace(tenant_id=7)

    response = asyncio.run(get_student_performance_analytics(user_id=404, db=object(), current_user=current_user))

    assert response["user_id"] == 404
    assert response["topic_mastery_heatmap"] == []
    assert response["meta"] == {"status": "pending", "last_updated": None, "is_rebuilding": True, "estimated_time": 30}
    assert queued["task_name"] == "jobs.refresh_student_analytics"
    assert queued["kwargs"] == {
        "tenant_id": 7,
        "user_id": 404,
        "dispatch_lock_key": "analytics:student:404",
        "dispatch_lock_token": "token-1",
    }
    assert queued["lock_key"] == "analytics:student:404"


def test_topic_performance_analytics_queues_when_snapshot_missing(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.AnalyticsService", StubAnalyticsService)
    queued = {}

    class _Cache:
        async def acquire_lock(self, key: str, *, ttl: int):
            queued["lock_key"] = key
            return "token-2"

        async def release_lock(self, key: str, token: str | None = None):
            queued["released"] = (key, token)
            return True

    monkeypatch.setattr("app.presentation.analytics_routes.CacheService", lambda: _Cache())
    monkeypatch.setattr(
        "app.presentation.analytics_routes.enqueue_job_with_options",
        lambda task_name, *, args=None, kwargs=None, countdown=None: queued.update(
            {"task_name": task_name, "kwargs": kwargs, "countdown": countdown}
        )
        or True,
    )
    current_user = SimpleNamespace(tenant_id=7)

    response = asyncio.run(get_topic_performance_analytics(topic_id=404, db=object(), current_user=current_user))

    assert response["topic_id"] == 404
    assert response["weakest_learners"] == []
    assert response["meta"] == {"status": "pending", "last_updated": None, "is_rebuilding": True, "estimated_time": 30}
    assert queued["task_name"] == "jobs.refresh_topic_analytics"
    assert queued["kwargs"] == {
        "tenant_id": 7,
        "topic_id": 404,
        "dispatch_lock_key": "analytics:topic:404",
        "dispatch_lock_token": "token-2",
    }
    assert queued["lock_key"] == "analytics:topic:404"


def test_student_performance_analytics_does_not_enqueue_duplicate_when_lock_exists(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.AnalyticsService", StubAnalyticsService)
    called = {"enqueued": False}

    class _Cache:
        async def acquire_lock(self, key: str, *, ttl: int):
            return None

    monkeypatch.setattr("app.presentation.analytics_routes.CacheService", lambda: _Cache())
    monkeypatch.setattr(
        "app.presentation.analytics_routes.enqueue_job_with_options",
        lambda *args, **kwargs: called.update({"enqueued": True}) or True,
    )

    response = asyncio.run(
        get_student_performance_analytics(user_id=404, db=object(), current_user=SimpleNamespace(tenant_id=7))
    )

    assert response["user_id"] == 404
    assert response["meta"] == {"status": "pending", "last_updated": None, "is_rebuilding": True, "estimated_time": 30}
    assert called["enqueued"] is False


class StubPrecomputedAnalyticsService:
    def __init__(self, _db):
        self.db = _db

    @staticmethod
    def _fresh_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    async def latest_tenant_dashboard(self, *, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "active_learners": 14,
            "weekly_event_count": 200,
            "average_topic_mastery": 68.2,
            "updated_at": self._fresh_timestamp(),
        }

    async def refresh_tenant_dashboard(self, *, tenant_id: int):
        return {"tenant_id": tenant_id, "active_learners": 15}

    async def latest_user_learning_summary(self, *, tenant_id: int, user_id: int):
        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "weekly_event_count": 18,
            "average_score": 72.5,
            "updated_at": self._fresh_timestamp(),
        }


class StubStalePrecomputedAnalyticsService(StubPrecomputedAnalyticsService):
    async def latest_tenant_dashboard(self, *, tenant_id: int):
        payload = await super().latest_tenant_dashboard(tenant_id=tenant_id)
        payload["updated_at"] = "2026-03-27T00:00:00Z"
        return payload

    async def latest_user_learning_summary(self, *, tenant_id: int, user_id: int):
        payload = await super().latest_user_learning_summary(tenant_id=tenant_id, user_id=user_id)
        payload["updated_at"] = "2026-03-27T00:00:00Z"
        return payload

    async def refresh_user_learning_summary(self, *, tenant_id: int, user_id: int):
        return {"tenant_id": tenant_id, "user_id": user_id, "average_score": 70.0}

    async def refresh_bundle(self, *, tenant_id: int, user_id: int | None = None, limit_users: int = 250):
        return {"tenant_id": tenant_id, "refreshed_users": 11, "tenant_dashboard": {"tenant_id": tenant_id}}


def test_precomputed_analytics_endpoints(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.PrecomputedAnalyticsService", StubPrecomputedAnalyticsService)
    queued = {}
    monkeypatch.setattr(
        "app.presentation.analytics_routes.enqueue_job_with_options",
        lambda task_name, *, args=None, kwargs=None, countdown=None: queued.update(
            {"task_name": task_name, "args": args, "kwargs": kwargs, "countdown": countdown}
        )
        or True,
    )

    class _Db:
        async def commit(self):
            return None

    teacher = SimpleNamespace(tenant_id=6)
    learner = SimpleNamespace(tenant_id=6, id=21)
    admin = SimpleNamespace(tenant_id=6)

    tenant_snapshot = asyncio.run(get_precomputed_tenant_dashboard(db=_Db(), current_user=teacher))
    assert tenant_snapshot["active_learners"] == 14
    assert tenant_snapshot["meta"]["status"] == "ready"
    assert tenant_snapshot["meta"]["last_updated"]
    assert tenant_snapshot["meta"]["is_rebuilding"] is False
    assert tenant_snapshot["meta"]["estimated_time"] is None

    user_snapshot = asyncio.run(get_precomputed_user_learning_summary(db=_Db(), current_user=learner))
    assert user_snapshot["average_score"] == 72.5
    assert user_snapshot["meta"]["status"] == "ready"
    assert user_snapshot["meta"]["last_updated"]
    assert user_snapshot["meta"]["is_rebuilding"] is False
    assert user_snapshot["meta"]["estimated_time"] is None

    refresh_result = asyncio.run(refresh_precomputed_analytics(db=_Db(), current_user=admin))
    assert refresh_result == {"status": "queued", "tenant_id": 6}
    assert queued["task_name"] == "jobs.refresh_precomputed_analytics"
    assert queued["kwargs"] == {"tenant_id": 6}


class StubDeadLetterRepository:
    def __init__(self, _db):
        self.db = _db

    async def list_recent_by_source_type(self, *, source_type: str, tenant_id: int | None, limit: int = 100):
        assert source_type == "analytics_job"
        return [
            SimpleNamespace(
                id=91,
                tenant_id=tenant_id,
                source_type="analytics_job",
                event_type="jobs.refresh_student_analytics",
                payload_json='{"tenant_id":7,"user_id":33}',
                error_message="projection failed",
                attempts=4,
                created_at=SimpleNamespace(isoformat=lambda: "2026-04-02T00:00:00+00:00"),
            )
        ]

    async def get_by_id(self, *, dead_letter_id: int, tenant_id: int | None = None):
        if dead_letter_id == 91:
            return SimpleNamespace(
                id=91,
                tenant_id=tenant_id,
                source_type="analytics_job",
                event_type="jobs.refresh_student_analytics",
                payload_json='{"tenant_id":7,"user_id":33}',
            )
        return None


def test_list_failed_analytics_jobs(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.DeadLetterRepository", StubDeadLetterRepository)

    result = asyncio.run(
        list_failed_analytics_jobs(
            limit=20,
            db=object(),
            current_user=SimpleNamespace(role=SimpleNamespace(value="admin"), tenant_id=7),
        )
    )

    assert result["items"][0]["job_name"] == "jobs.refresh_student_analytics"
    assert result["items"][0]["payload"]["user_id"] == 33


def test_retry_failed_analytics_job(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.DeadLetterRepository", StubDeadLetterRepository)
    monkeypatch.setattr(
        "app.presentation.analytics_routes._enqueue_deduplicated_analytics_job",
        lambda **kwargs: asyncio.sleep(0, result=True),
    )

    result = asyncio.run(
        retry_failed_analytics_job(
            dead_letter_id=91,
            db=object(),
            current_user=SimpleNamespace(role=SimpleNamespace(value="admin"), tenant_id=7),
        )
    )

    assert result["status"] == "queued"
    assert result["job_name"] == "jobs.refresh_student_analytics"


def test_retry_failed_analytics_job_missing(monkeypatch):
    monkeypatch.setattr("app.presentation.analytics_routes.DeadLetterRepository", StubDeadLetterRepository)

    try:
        asyncio.run(
            retry_failed_analytics_job(
                dead_letter_id=999,
                db=object(),
                current_user=SimpleNamespace(role=SimpleNamespace(value="admin"), tenant_id=7),
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        assert False, "Expected HTTPException"
