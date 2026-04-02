import asyncio
from types import SimpleNamespace

from app.presentation.dashboard_routes import get_admin_dashboard, get_student_dashboard


class StubDashboardService:
    def __init__(self, _db):
        self.db = _db

    async def student_dashboard(self, *, user_id: int, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "roadmap_progress": {
                "total_steps": 5,
                "completed_steps": 2,
                "in_progress_steps": 1,
                "completion_percent": 40,
            },
            "recommended_topics": [10, 11],
            "mentor_suggestions": ["Finish one roadmap step.", "Review weak topics."],
        }

    async def admin_dashboard(self, *, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "total_users": 12,
            "active_learners": 8,
            "roadmap_completions": 55.5,
            "diagnostics_taken": 18,
            "learners": [],
        }


def test_get_student_dashboard(monkeypatch):
    monkeypatch.setattr("app.presentation.dashboard_routes.DashboardService", StubDashboardService)
    current_user = SimpleNamespace(id=3, tenant_id=5)

    response = asyncio.run(get_student_dashboard(db=object(), current_user=current_user))

    assert response["tenant_id"] == 5
    assert response["roadmap_progress"]["completion_percent"] == 40
    assert response["recommended_topics"] == [10, 11]


def test_get_admin_dashboard(monkeypatch):
    monkeypatch.setattr("app.presentation.dashboard_routes.DashboardService", StubDashboardService)
    current_user = SimpleNamespace(tenant_id=9)

    response = asyncio.run(get_admin_dashboard(db=object(), current_user=current_user))

    assert response["tenant_id"] == 9
    assert response["total_users"] == 12
    assert response["diagnostics_taken"] == 18
