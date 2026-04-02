import asyncio
from types import SimpleNamespace

from app.presentation import notification_routes


class _FakeNotificationService:
    last_list = None
    last_mark_read = None
    last_generate = None

    def __init__(self, _db):
        self.db = _db

    async def list_for_user(self, *, tenant_id: int, user_id: int, unread_only: bool = False, limit: int = 30):
        _FakeNotificationService.last_list = (tenant_id, user_id, unread_only, limit)
        return [
            {
                "id": 10,
                "notification_type": "deadline",
                "severity": "warning",
                "title": "Deadline approaching",
                "message": "Complete your next topic today.",
                "action_url": "/student/roadmap",
                "created_at": "2026-03-25T00:00:00Z",
                "read_at": None,
            }
        ]

    async def mark_read(self, *, tenant_id: int, user_id: int, notification_id: int):
        _FakeNotificationService.last_mark_read = (tenant_id, user_id, notification_id)
        return {
            "id": notification_id,
            "notification_type": "deadline",
            "severity": "warning",
            "title": "Deadline approaching",
            "message": "Complete your next topic today.",
            "action_url": "/student/roadmap",
            "created_at": "2026-03-25T00:00:00Z",
            "read_at": "2026-03-25T01:00:00Z",
        }

    async def generate_due_notifications(self, *, tenant_id: int | None = None, limit_users: int = 100):
        _FakeNotificationService.last_generate = (tenant_id, limit_users)
        return 4


def _user():
    return SimpleNamespace(id=7, tenant_id=3)


def _admin():
    return SimpleNamespace(id=8, tenant_id=3, role=SimpleNamespace(value="admin"))


def test_notification_routes(monkeypatch):
    monkeypatch.setattr(notification_routes, "NotificationService", _FakeNotificationService)

    async def _run():
        listed = await notification_routes.list_notifications(
            unread_only=True,
            limit=20,
            db=object(),
            current_user=_user(),
        )
        assert listed["notifications"][0]["title"] == "Deadline approaching"
        assert _FakeNotificationService.last_list == (3, 7, True, 20)

        read = await notification_routes.mark_notification_read(
            notification_id=10,
            db=object(),
            current_user=_user(),
        )
        assert read["read_at"] is not None
        assert _FakeNotificationService.last_mark_read == (3, 7, 10)

    asyncio.run(_run())


def test_generate_notifications_route(monkeypatch):
    monkeypatch.setattr(notification_routes, "NotificationService", _FakeNotificationService)

    class _Db:
        async def commit(self):
            return None

    async def _run():
        result = await notification_routes.generate_notifications(
            limit_users=50,
            db=_Db(),
            current_user=_admin(),
        )
        assert result == {"tenant_id": 3, "created": 4}
        assert _FakeNotificationService.last_generate == (3, 50)

    asyncio.run(_run())
