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
