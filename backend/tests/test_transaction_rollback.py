import asyncio

import pytest

from app.application.services.auth_service import AuthService
from app.application.services.diagnostic_service import DiagnosticService
from app.application.services.roadmap_service import RoadmapService
from app.domain.models.user import UserRole


class _Session:
    def __init__(self):
        self.rollback_called = False

    async def commit(self):
        return None

    async def rollback(self):
        self.rollback_called = True


def test_auth_register_rolls_back_on_create_failure():
    class _TenantRepo:
        async def get_by_id(self, tenant_id):
            return object()

    class _UserRepo:
        async def get_by_email(self, email, *, tenant_id=None):
            return None

        async def create(self, tenant_id, email, password_hash, role, created_at):
            raise RuntimeError("db write failed")

    async def _run():
        session = _Session()
        service = AuthService(session)
        service.tenant_repository = _TenantRepo()
        service.user_repository = _UserRepo()

        with pytest.raises(RuntimeError):
            await service.register(
                email="x@y.com",
                password="secure123",
            )

        assert session.rollback_called is True

    asyncio.run(_run())


def test_diagnostic_submit_rolls_back_on_missing_question():
    class _DiagRepo:
        async def get_test_for_user(self, test_id, user_id, tenant_id, for_update=False):
            return object()

    class _TopicRepo:
        async def get_question(self, question_id):
            return None

        async def list_questions_by_ids(self, *, tenant_id, question_ids):
            return []

    async def _run():
        session = _Session()
        service = DiagnosticService(session)
        service.diagnostic_repository = _DiagRepo()
        service.topic_repository = _TopicRepo()

        with pytest.raises(Exception):
            await service.submit_answers(
                test_id=1,
                user_id=1,
                tenant_id=1,
                answers=[{"question_id": 99, "user_answer": "x", "score": 0.0, "time_taken": 1.0}],
            )

        assert session.rollback_called is True

    asyncio.run(_run())


def test_roadmap_generate_rolls_back_on_step_failure():
    class _DiagRepo:
        async def topic_scores_for_test(self, test_id, user_id, tenant_id):
            return {101: 40.0}

    class _TopicRepo:
        async def get_prerequisite_edges(self, tenant_id=None):
            return []

    class _RoadmapRepo:
        class _RM:
            id = 1
            steps = []
            status = "generating"
            error_message = None

        def __init__(self):
            self.roadmap = self._RM()

        async def get_by_identity(self, *, user_id, goal_id, test_id, tenant_id, for_update=False):
            return self.roadmap

        async def create_roadmap(self, user_id, goal_id, test_id, generated_at, status="generating", error_message=None):
            self.roadmap.status = status
            self.roadmap.error_message = error_message
            return self.roadmap

        async def mark_status(self, roadmap, *, status, error_message=None):
            roadmap.status = status
            roadmap.error_message = error_message
            return roadmap

        async def clear_steps(self, roadmap):
            return None

        async def add_step(
            self,
            roadmap_id,
            topic_id,
            deadline,
            estimated_time_hours=4.0,
            difficulty="medium",
            priority=1,
            progress_status="pending",
            step_type="core",
            rationale=None,
        ):
            raise RuntimeError("step insert failed")

    async def _run():
        session = _Session()
        service = RoadmapService(session)
        service.diagnostic_repository = _DiagRepo()
        service.topic_repository = _TopicRepo()
        repo = _RoadmapRepo()
        service.roadmap_repository = repo

        with pytest.raises(RuntimeError):
            await service.generate(user_id=1, tenant_id=1, goal_id=1, test_id=1)

        assert session.rollback_called is True
        assert repo.roadmap.status == "failed"
        assert repo.roadmap.error_message == "step insert failed"

    asyncio.run(_run())
