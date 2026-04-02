import sys
from types import ModuleType, SimpleNamespace


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
