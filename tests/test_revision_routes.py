import asyncio
from types import SimpleNamespace

from app.presentation import revision_routes


class _FakeRetentionService:
    last_call = None

    def __init__(self, session):
        self.session = session

    async def revisions_due_today(self, *, tenant_id: int, user_id: int):
        _FakeRetentionService.last_call = {"tenant_id": tenant_id, "user_id": user_id}
        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "generated_at": "2026-03-29T00:00:00Z",
            "due_count": 1,
            "revisions": [
                {
                    "topic_id": 11,
                    "topic_name": "Graph Traversal",
                    "score": 62.0,
                    "retention_score": 48.0,
                    "revision_interval_days": 2,
                    "review_due_at": "2026-03-29T00:00:00Z",
                    "last_seen": "2026-03-27T00:00:00Z",
                    "is_due": True,
                }
            ],
        }


def test_revision_today_route(monkeypatch):
    monkeypatch.setattr(revision_routes, "RetentionService", _FakeRetentionService)

    async def _run():
        response = await revision_routes.revision_today(
            db=object(),
            current_user=SimpleNamespace(id=7, tenant_id=3),
        )
        assert response["due_count"] == 1
        assert response["revisions"][0]["topic_id"] == 11
        assert _FakeRetentionService.last_call == {"tenant_id": 3, "user_id": 7}

    asyncio.run(_run())
