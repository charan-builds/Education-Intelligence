import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.presentation import outbox_routes


class _DummySession:
    pass


class _FakeOutboxService:
    last_list_args = None
    last_flush_limit = None
    last_requeue_args = None
    last_stats_tenant = None
    last_requeue_one_args = None
    last_recover_limit = None

    def __init__(self, session):
        self.session = session

    async def list_events(self, *, status: str, tenant_id: int | None, limit: int, offset: int):
        _FakeOutboxService.last_list_args = {
            "status": status,
            "tenant_id": tenant_id,
            "limit": limit,
            "offset": offset,
        }
        return []

    async def flush_pending_events(self, *, limit: int = 100):
        _FakeOutboxService.last_flush_limit = limit
        return 3

    async def requeue_dead_events(self, *, tenant_id: int | None, limit: int):
        _FakeOutboxService.last_requeue_args = {"tenant_id": tenant_id, "limit": limit}
        return 2

    async def get_stats(self, *, tenant_id: int | None):
        _FakeOutboxService.last_stats_tenant = tenant_id
        return {"pending": 11, "processing": 2, "dead": 3, "dispatched": 20}

    async def requeue_dead_event_by_id(self, *, event_id: int, tenant_id: int | None):
        _FakeOutboxService.last_requeue_one_args = {"event_id": event_id, "tenant_id": tenant_id}
        return event_id == 99

    async def recover_stuck_processing_events(self, *, limit: int = 500):
        _FakeOutboxService.last_recover_limit = limit
        return 4


def _user(role: str, tenant_id: int = 10):
    return SimpleNamespace(role=SimpleNamespace(value=role), tenant_id=tenant_id)


def test_list_outbox_forbidden_for_student(monkeypatch):
    monkeypatch.setattr(outbox_routes, "OutboxService", _FakeOutboxService)

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await outbox_routes.list_outbox_events(
                event_status="pending",
                limit=10,
                offset=0,
                db=_DummySession(),
                current_user=_user("student"),
            )
        assert exc.value.status_code == 403

    asyncio.run(_run())


def test_list_outbox_admin_scoped_to_tenant(monkeypatch):
    monkeypatch.setattr(outbox_routes, "OutboxService", _FakeOutboxService)

    async def _run():
        await outbox_routes.list_outbox_events(
            event_status="dead",
            limit=5,
            offset=2,
            db=_DummySession(),
            current_user=_user("admin", tenant_id=42),
        )
        assert _FakeOutboxService.last_list_args == {
            "status": "dead",
            "tenant_id": 42,
            "limit": 5,
            "offset": 2,
        }

    asyncio.run(_run())


def test_list_outbox_super_admin_cross_tenant(monkeypatch):
    monkeypatch.setattr(outbox_routes, "OutboxService", _FakeOutboxService)

    async def _run():
        await outbox_routes.list_outbox_events(
            event_status="dispatched",
            limit=20,
            offset=0,
            db=_DummySession(),
            current_user=_user("super_admin", tenant_id=1),
        )
        assert _FakeOutboxService.last_list_args["tenant_id"] is None

    asyncio.run(_run())


def test_flush_and_requeue_admin(monkeypatch):
    monkeypatch.setattr(outbox_routes, "OutboxService", _FakeOutboxService)

    async def _run():
        flush_result = await outbox_routes.flush_outbox_events(
            limit=50,
            db=_DummySession(),
            current_user=_user("admin", tenant_id=7),
        )
        assert flush_result.dispatched == 3
        assert _FakeOutboxService.last_flush_limit == 50

        requeue_result = await outbox_routes.requeue_dead_outbox_events(
            limit=30,
            db=_DummySession(),
            current_user=_user("admin", tenant_id=7),
        )
        assert requeue_result.requeued == 2
        assert _FakeOutboxService.last_requeue_args == {"tenant_id": 7, "limit": 30}

    asyncio.run(_run())


def test_stats_super_admin(monkeypatch):
    monkeypatch.setattr(outbox_routes, "OutboxService", _FakeOutboxService)

    async def _run():
        result = await outbox_routes.outbox_stats(
            db=_DummySession(),
            current_user=_user("super_admin", tenant_id=7),
        )
        assert result.pending == 11
        assert result.processing == 2
        assert result.dead == 3
        assert result.dispatched == 20
        assert _FakeOutboxService.last_stats_tenant is None

    asyncio.run(_run())


def test_requeue_one_dead_event(monkeypatch):
    monkeypatch.setattr(outbox_routes, "OutboxService", _FakeOutboxService)

    async def _run():
        ok = await outbox_routes.requeue_one_dead_outbox_event(
            event_id=99,
            db=_DummySession(),
            current_user=_user("admin", tenant_id=12),
        )
        assert ok.requeued is True
        assert _FakeOutboxService.last_requeue_one_args == {"event_id": 99, "tenant_id": 12}

        with pytest.raises(HTTPException) as exc:
            await outbox_routes.requeue_one_dead_outbox_event(
                event_id=100,
                db=_DummySession(),
                current_user=_user("admin", tenant_id=12),
            )
        assert exc.value.status_code == 404

    asyncio.run(_run())


def test_recover_stuck_admin(monkeypatch):
    monkeypatch.setattr(outbox_routes, "OutboxService", _FakeOutboxService)

    async def _run():
        result = await outbox_routes.recover_stuck_outbox_events(
            limit=123,
            db=_DummySession(),
            current_user=_user("admin", tenant_id=5),
        )
        assert result.recovered == 4
        assert _FakeOutboxService.last_recover_limit == 123

    asyncio.run(_run())
