import sys
from types import ModuleType, SimpleNamespace
from pathlib import Path

import pytest


fake_celery = ModuleType("celery")
fake_celery_signals = ModuleType("celery.signals")


class _FakeSignal:
    def connect(self, *_args, **_kwargs):
        return None


class _FakeCelery:
    def __init__(self, *args, **kwargs):
        _ = args, kwargs
        self.conf = SimpleNamespace(update=lambda **kw: None)

    def config_from_object(self, *args, **kwargs):
        _ = args, kwargs

    def send_task(self, *args, **kwargs):
        _ = args, kwargs
        return None

    def autodiscover_tasks(self, *args, **kwargs):
        _ = args, kwargs

    def task(self, *args, **kwargs):
        _ = args, kwargs

        def _decorator(func):
            return func

        return _decorator


fake_celery.Celery = _FakeCelery
fake_celery_signals.before_task_publish = _FakeSignal()
fake_celery_signals.task_failure = _FakeSignal()
fake_celery_signals.task_postrun = _FakeSignal()
fake_celery_signals.task_prerun = _FakeSignal()
fake_celery_signals.task_retry = _FakeSignal()
sys.modules.setdefault("celery", fake_celery)
sys.modules.setdefault("celery.signals", fake_celery_signals)

from app.infrastructure.jobs import tasks
from app.application.services.analytics_snapshot_types import (
    INSTITUTION_DASHBOARD_SNAPSHOT,
    SYSTEM_SUMMARY_SNAPSHOT,
    TEACHER_DASHBOARD_SNAPSHOT,
    USER_DASHBOARD_SNAPSHOT,
    normalize_snapshot_type,
)


def test_all_tasks_declare_explicit_queue() -> None:
    text = Path("backend/app/infrastructure/jobs/tasks.py").read_text(encoding="utf-8")
    assert "@celery_app.task" not in text


def test_enforce_queue_raises_without_queue() -> None:
    def _task_without_queue():
        return None

    with pytest.raises(ValueError, match="missing queue assignment"):
        tasks.enforce_queue(_task_without_queue)


def test_generate_notifications_logs_safe_extra_keys(monkeypatch):
    def _fake_run_async(coro):
        coro.close()
        return {"created": 7, "tenant_id": 3}

    monkeypatch.setattr(
        tasks,
        "_run_async",
        _fake_run_async,
    )
    monkeypatch.setattr(tasks, "_record_task_duration", lambda *args, **kwargs: None)

    logged = {}

    class _Logger:
        def info(self, message, *, extra):
            logged["message"] = message
            logged["extra"] = extra

    monkeypatch.setattr(tasks, "logger", _Logger())

    result = tasks.generate_notifications(tenant_id=3, limit_users=25)

    assert result == {"created": 7, "tenant_id": 3}
    assert logged["message"] == "generate_notifications completed"
    assert logged["extra"] == {"tenant_id": 3, "notifications_created": 7}


def test_refresh_student_analytics_releases_dispatch_lock(monkeypatch):
    released = {}

    def _fake_run_async(coro):
        name = coro.cr_code.co_name
        coro.close()
        if name == "_run_refresh_student_analytics":
            return {"status": "processed", "tenant_id": 3, "user_id": 9}
        if name == "_release_dispatch_lock":
            released["called"] = True
            return None
        return None

    monkeypatch.setattr(tasks, "_run_async", _fake_run_async)
    monkeypatch.setattr(tasks, "_record_task_duration", lambda *args, **kwargs: None)

    result = tasks.refresh_student_analytics(
        tenant_id=3,
        user_id=9,
        dispatch_lock_key="analytics:student:9",
        dispatch_lock_token="token-9",
    )

    assert result["status"] == "processed"
    assert released["called"] is True


def test_refresh_student_analytics_schedules_retry(monkeypatch):
    queued = {}

    def _fake_run_async(coro):
        name = coro.cr_code.co_name
        coro.close()
        if name == "_run_refresh_student_analytics":
            raise RuntimeError("boom")
        return None

    monkeypatch.setattr(tasks, "_run_async", _fake_run_async)
    monkeypatch.setattr(tasks, "_record_task_duration", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        tasks,
        "enqueue_job_with_options",
        lambda task_name, *, args=None, kwargs=None, countdown=None: queued.update(
            {"task_name": task_name, "kwargs": kwargs, "countdown": countdown}
        )
        or True,
    )

    result = tasks.refresh_student_analytics(
        tenant_id=3,
        user_id=9,
        delivery_attempt=1,
        dispatch_lock_key="analytics:student:9",
        dispatch_lock_token="token-9",
    )

    assert result["status"] == "retry_scheduled"
    assert queued["task_name"] == "jobs.refresh_student_analytics"
    assert queued["kwargs"]["delivery_attempt"] == 2
    assert queued["kwargs"]["dispatch_lock_key"] == "analytics:student:9"


def test_refresh_topic_analytics_moves_to_dead_letter(monkeypatch):
    dead_letter = {}
    released = {}

    def _fake_run_async(coro):
        name = coro.cr_code.co_name
        coro.close()
        if name == "_run_refresh_topic_analytics":
            raise RuntimeError("bad topic rebuild")
        if name == "_create_analytics_dead_letter":
            dead_letter["called"] = True
            return None
        if name == "_release_dispatch_lock":
            released["called"] = True
            return None
        return None

    monkeypatch.setattr(tasks, "_run_async", _fake_run_async)
    monkeypatch.setattr(tasks, "_record_task_duration", lambda *args, **kwargs: None)
    monkeypatch.setattr(tasks, "logger", SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, exception=lambda *a, **k: None))
    monkeypatch.setattr(tasks, "enqueue_job_with_options", lambda *args, **kwargs: False)

    result = tasks.refresh_topic_analytics(
        tenant_id=3,
        topic_id=12,
        delivery_attempt=4,
        dispatch_lock_key="analytics:topic:12",
        dispatch_lock_token="token-12",
    )

    assert result["status"] == "dead"
    assert dead_letter["called"] is True
    assert released["called"] is True


def test_refresh_precomputed_analytics_uses_scheduled_projection_path(monkeypatch):
    calls = []

    class _Service:
        def __init__(self, _session):
            return None

        async def refresh_scheduled_tenant_projections(self, *, tenant_id: int, limit_users: int = 250):
            calls.append(("scheduled", tenant_id, limit_users))
            return {"tenant_id": tenant_id}

        async def refresh_platform_overview(self):
            calls.append(("platform", None, None))
            return {"status": "ok"}

    class _Ctx:
        async def __aenter__(self):
            class _Session:
                async def commit(self):
                    return None

            return _Session()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def _fake_list_student_tenant_ids(limit: int = 250):
        _ = limit
        return [3, 4]

    monkeypatch.setattr(tasks, "PrecomputedAnalyticsService", _Service)
    monkeypatch.setattr(tasks, "open_tenant_session", lambda **kwargs: _Ctx())
    monkeypatch.setattr(tasks, "_list_student_tenant_ids", _fake_list_student_tenant_ids)
    class _GlobalSession:
        async def commit(self):
            return None

    monkeypatch.setattr(tasks, "_run_global_super_admin_job", lambda **kwargs: kwargs["operation"](_GlobalSession()))

    result = tasks._run_async(tasks._run_refresh_precomputed_analytics(limit_users=25))

    assert result == {"refreshed_tenants": 2, "tenant_id": None}
    assert ("scheduled", 3, 25) in calls
    assert ("scheduled", 4, 25) in calls
    assert ("platform", None, None) in calls


def test_refresh_active_tenant_analytics_uses_recently_active_tenants(monkeypatch):
    calls = []

    class _Service:
        def __init__(self, _session):
            return None

        async def refresh_scheduled_tenant_projections(self, *, tenant_id: int, limit_users: int = 250):
            calls.append(("scheduled", tenant_id, limit_users))
            return {"tenant_id": tenant_id, "refreshed_users": 2}

    class _Ctx:
        async def __aenter__(self):
            class _Session:
                async def commit(self):
                    return None

            return _Session()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def _fake_list_active_tenant_ids(*, limit: int, active_within_minutes: int = 5):
        calls.append(("active_tenants", limit, active_within_minutes))
        return [8, 13]

    monkeypatch.setattr(tasks, "PrecomputedAnalyticsService", _Service)
    monkeypatch.setattr(tasks, "open_tenant_session", lambda **kwargs: _Ctx())
    monkeypatch.setattr(tasks, "_list_active_tenant_ids", _fake_list_active_tenant_ids)

    result = tasks._run_async(
        tasks._run_refresh_active_tenant_analytics(limit_users=15, tenant_limit=10, active_within_minutes=7)
    )

    assert result == {"refreshed_tenants": 2, "refreshed_users": 4}
    assert ("active_tenants", 10, 7) in calls
    assert ("scheduled", 8, 15) in calls
    assert ("scheduled", 13, 15) in calls


@pytest.mark.asyncio
async def test_enqueue_snapshot_rebuild_skips_when_lock_exists(monkeypatch):
    class _Cache:
        async def acquire_lock(self, key: str, *, ttl: int):
            _ = key, ttl
            return None

    enqueued = {"called": False}
    monkeypatch.setattr(tasks, "CacheService", lambda: _Cache())
    monkeypatch.setattr(
        tasks,
        "enqueue_job_with_options",
        lambda *args, **kwargs: enqueued.update({"called": True}) or True,
    )

    queued = await tasks.enqueue_snapshot_rebuild(tenant_id=7, snapshot_type="tenant_dashboard")

    assert queued is False
    assert enqueued["called"] is False


@pytest.mark.asyncio
async def test_enqueue_snapshot_rebuild_skips_when_tenant_limit_reached(monkeypatch):
    released = {}

    class _Cache:
        async def acquire_lock(self, key: str, *, ttl: int):
            released["acquired"] = (key, ttl)
            return "token-1"

        async def increment_counter(self, key: str, *, ttl: int | None = None):
            released["counter"] = (key, ttl)
            return 4

        async def decrement_counter(self, key: str):
            released["decremented"] = key
            return 3

        async def release_lock(self, key: str, token: str | None = None):
            released["released"] = (key, token)
            return True

    enqueued = {"called": False}
    monkeypatch.setattr(tasks, "CacheService", lambda: _Cache())
    monkeypatch.setattr(
        tasks,
        "enqueue_job_with_options",
        lambda *args, **kwargs: enqueued.update({"called": True}) or True,
    )

    queued = await tasks.enqueue_snapshot_rebuild(tenant_id=7, snapshot_type="tenant_dashboard")

    assert queued is False
    assert released["decremented"] == "analytics:tenant_jobs:7"
    assert released["released"] == ("analytics:lock:7:tenant_dashboard", "token-1")
    assert enqueued["called"] is False


@pytest.mark.asyncio
async def test_enqueue_snapshot_rebuild_releases_lock_when_enqueue_fails(monkeypatch):
    released = {}

    class _Cache:
        async def acquire_lock(self, key: str, *, ttl: int):
            released["acquired"] = (key, ttl)
            return "token-1"

        async def increment_counter(self, key: str, *, ttl: int | None = None):
            released["counter"] = (key, ttl)
            return 1

        async def decrement_counter(self, key: str):
            released["decremented"] = key
            return 0

        async def release_lock(self, key: str, token: str | None = None):
            released["released"] = (key, token)
            return True

    monkeypatch.setattr(tasks, "CacheService", lambda: _Cache())
    monkeypatch.setattr(tasks, "enqueue_job_with_options", lambda *args, **kwargs: False)

    queued = await tasks.enqueue_snapshot_rebuild(tenant_id=9, snapshot_type="learning_trends")

    assert queued is False
    assert released["decremented"] == "analytics:tenant_jobs:9"
    assert released["released"] == ("analytics:lock:9:learning_trends", "token-1")


def test_rebuild_snapshot_releases_dispatch_lock(monkeypatch):
    released = {}

    def _fake_run_async(coro):
        name = coro.cr_code.co_name
        coro.close()
        if name == "_run_rebuild_snapshot":
            return {"status": "processed", "tenant_id": 3, "snapshot": "tenant_dashboard"}
        if name == "_release_dispatch_lock":
            released["called"] = True
            return None
        if name == "_release_tenant_job_counter":
            released["counter_called"] = True
            return None
        return None

    monkeypatch.setattr(tasks, "_run_async", _fake_run_async)

    result = tasks.rebuild_snapshot(
        tenant_id=3,
        snapshot_type="tenant_dashboard",
        dispatch_lock_key="analytics:lock:3:tenant_dashboard",
        dispatch_lock_token="token-3",
    )

    assert result["status"] == "processed"
    assert released["called"] is True
    assert released["counter_called"] is True


def test_snapshot_type_normalization_and_rebuild_branching(monkeypatch):
    assert normalize_snapshot_type("tenant_dashboard") == INSTITUTION_DASHBOARD_SNAPSHOT
    assert normalize_snapshot_type("platform_overview") == SYSTEM_SUMMARY_SNAPSHOT
    assert normalize_snapshot_type("user_learning_summary") == USER_DASHBOARD_SNAPSHOT

    async def _institution(_tenant_id: int):
        return {"status": "processed", "snapshot": INSTITUTION_DASHBOARD_SNAPSHOT}

    async def _teacher(_tenant_id: int):
        return {"status": "processed", "snapshot": TEACHER_DASHBOARD_SNAPSHOT}

    monkeypatch.setattr(tasks, "_run_refresh_roadmap_progress_summary", _teacher)

    class _Ctx:
        async def __aenter__(self):
            class _Session:
                async def commit(self):
                    return None

            return _Session()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _Service:
        def __init__(self, _session):
            return None

        async def refresh_tenant_dashboard(self, *, tenant_id: int):
            return {"tenant_id": tenant_id}

        async def refresh_platform_overview(self):
            return {"status": "ok"}

    monkeypatch.setattr(tasks, "open_tenant_session", lambda **kwargs: _Ctx())
    monkeypatch.setattr(tasks, "PrecomputedAnalyticsService", _Service)

    institution = tasks._run_async(tasks._run_rebuild_snapshot(tenant_id=9, snapshot_type=INSTITUTION_DASHBOARD_SNAPSHOT))
    teacher = tasks._run_async(tasks._run_rebuild_snapshot(tenant_id=9, snapshot_type=TEACHER_DASHBOARD_SNAPSHOT))

    assert institution["snapshot"] == INSTITUTION_DASHBOARD_SNAPSHOT
    assert teacher["snapshot"] == TEACHER_DASHBOARD_SNAPSHOT
