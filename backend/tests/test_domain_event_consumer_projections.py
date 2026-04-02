import asyncio

from app.application.services.domain_event_consumer_service import DomainEventConsumerService


class _Session:
    async def execute(self, _stmt):
        class _Result:
            def all(self):
                return [(7, "SQL")]

        return _Result()


class _AnalyticsService:
    def __init__(self):
        self.calls: list[tuple[str, int, int]] = []

    async def refresh_user_diagnostic_summary(self, *, tenant_id: int, user_id: int) -> dict:
        self.calls.append(("diagnostic", tenant_id, user_id))
        return {"average_score": 82.5, "user_id": user_id}

    async def refresh_user_roadmap_stats(self, *, tenant_id: int, user_id: int) -> dict:
        self.calls.append(("roadmap", tenant_id, user_id))
        return {"completion_percent": 40, "user_id": user_id}

    async def refresh_student_performance_analytics(self, *, tenant_id: int, user_id: int) -> dict:
        self.calls.append(("student", tenant_id, user_id))
        return {"user_id": user_id}

    async def refresh_topic_performance_analytics(self, *, tenant_id: int, topic_id: int, topic_name: str) -> dict:
        self.calls.append((f"topic:{topic_name}", tenant_id, topic_id))
        return {"topic_id": topic_id}

    async def refresh_bundle(self, *, tenant_id: int, user_id: int | None = None, limit_users: int = 250) -> dict:
        raise AssertionError("refresh_bundle should not be used by domain event consumers")


class _SkillVectorService:
    def __init__(self):
        self.calls: list[tuple[int, int, int, str]] = []

    async def update_from_progress(self, *, tenant_id: int, user_id: int, topic_id: int, progress_status: str) -> dict:
        self.calls.append((tenant_id, user_id, topic_id, progress_status))
        return {"topic_id": topic_id, "mastery_score": 57.5, "confidence_score": 0.31}


class _NotificationService:
    def __init__(self):
        self.created: list[dict] = []

    async def create_notification(self, **kwargs):
        self.created.append(kwargs)
        return kwargs


class _Cache:
    def __init__(self):
        self.values: dict[str, dict] = {}

    @staticmethod
    def build_key(namespace: str, **parts) -> str:
        suffix = ":".join(f"{name}={parts[name]}" for name in sorted(parts))
        return f"{namespace}:{suffix}"

    async def get(self, key: str):
        return self.values.get(key)

    async def set(self, key: str, value: dict, ttl: int = 300):
        self.values[key] = {"value": value, "ttl": ttl}
        return True


def test_domain_event_consumer_uses_granular_projections(monkeypatch):
    async def _run():
        service = DomainEventConsumerService(_Session())
        service.analytics_service = _AnalyticsService()
        service.skill_vector_service = _SkillVectorService()
        service.notification_service = _NotificationService()
        service.cache = _Cache()

        scheduled: list[tuple[str, dict, int | None]] = []
        monkeypatch.setattr(
            "app.application.services.domain_event_consumer_service.enqueue_job_with_options",
            lambda task_name, *, args=None, kwargs=None, countdown=None: scheduled.append((task_name, kwargs or {}, countdown)) or True,
        )

        diagnostic_result = await service.handle_event(
            envelope={
                "event_name": "diagnostic_completed",
                "payload": {"tenant_id": 1, "user_id": 2, "diagnostic_test_id": 3},
            }
        )
        assert diagnostic_result["projection"] == "user_diagnostic_summary"
        assert service.analytics_service.calls == [("diagnostic", 1, 2), ("student", 1, 2), ("topic:SQL", 1, 7)]

        roadmap_result = await service.handle_event(
            envelope={
                "event_name": "roadmap_generated",
                "payload": {"tenant_id": 1, "user_id": 2, "roadmap_id": 5},
            }
        )
        assert roadmap_result["projection"] == "user_roadmap_stats"
        assert service.analytics_service.calls[-1] == ("roadmap", 1, 2)

        progress_result = await service.handle_event(
            envelope={
                "event_name": "user_progress_updated",
                "payload": {"tenant_id": 1, "user_id": 2, "step_id": 9, "topic_id": 7, "progress_status": "completed"},
            }
        )
        assert progress_result["projection"] == "skill_vector"
        assert service.skill_vector_service.calls == [(1, 2, 7, "completed")]
        assert scheduled == [
            ("jobs.refresh_user_projection", {"tenant_id": 1, "user_id": 2, "projection_type": "user_roadmap_stats"}, 5)
        ]

        await service.handle_event(
            envelope={
                "event_name": "user_progress_updated",
                "payload": {"tenant_id": 1, "user_id": 2, "step_id": 10, "topic_id": 8, "progress_status": "in_progress"},
            }
        )
        assert len(scheduled) == 1

    asyncio.run(_run())
