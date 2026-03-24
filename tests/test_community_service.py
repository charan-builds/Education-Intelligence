import asyncio
from types import SimpleNamespace

import pytest

from app.application.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.application.services.community_service import CommunityService


class _Session:
    async def commit(self):
        return None


class _CommunityRepository:
    def __init__(self):
        self.session = _Session()
        self.topic = SimpleNamespace(id=1, name="Machine Learning")
        self.community = SimpleNamespace(
            id=7,
            tenant_id=5,
            topic_id=1,
            name="ML Community",
            description="Peer discussion",
            created_at="2026-03-14T00:00:00Z",
        )
        self.member = None
        self.thread = SimpleNamespace(
            id=11,
            tenant_id=5,
            community_id=7,
            author_user_id=3,
            title="Need help",
            body="How do I revise?",
            is_resolved=False,
            created_at="2026-03-14T00:00:00Z",
        )
        self.badge = SimpleNamespace(
            id=4,
            tenant_id=5,
            user_id=2,
            name="Top Mentor",
            description="Helpful mentor",
            awarded_for="mentorship",
            awarded_at="2026-03-14T00:00:00Z",
        )
        self.deleted_community = None
        self.deleted_badge = None

    async def get_topic(self, topic_id: int):
        return self.topic if topic_id == 1 else None

    async def get_community_by_topic(self, tenant_id: int, topic_id: int):
        _ = tenant_id
        return self.community if topic_id == self.community.topic_id else None

    async def create_community(self, **kwargs):
        return SimpleNamespace(id=8, created_at="2026-03-14T00:00:00Z", **kwargs)

    async def get_community(self, tenant_id: int, community_id: int):
        if tenant_id == self.community.tenant_id and community_id == self.community.id:
            return self.community
        return None

    async def delete_community(self, community):
        self.deleted_community = community

    async def get_member(self, tenant_id: int, community_id: int, user_id: int):
        _ = tenant_id, community_id, user_id
        return self.member

    async def create_member(self, **kwargs):
        self.member = SimpleNamespace(id=10, joined_at="2026-03-14T00:00:00Z", **kwargs)
        return self.member

    async def create_thread(self, **kwargs):
        self.thread = SimpleNamespace(id=12, is_resolved=False, created_at="2026-03-14T00:00:00Z", **kwargs)
        return self.thread

    async def get_thread(self, tenant_id: int, thread_id: int):
        if tenant_id == self.thread.tenant_id and thread_id == self.thread.id:
            return self.thread
        return None

    async def update_thread_resolution(self, thread, is_resolved: bool):
        thread.is_resolved = is_resolved
        return thread

    async def create_badge(self, **kwargs):
        self.badge = SimpleNamespace(id=9, awarded_at="2026-03-14T00:00:00Z", **kwargs)
        return self.badge

    async def get_badge(self, tenant_id: int, badge_id: int):
        if tenant_id == self.badge.tenant_id and badge_id == self.badge.id:
            return self.badge
        return None

    async def delete_badge(self, badge):
        self.deleted_badge = badge


class _UserRepository:
    def __init__(self):
        self.user = SimpleNamespace(id=2, tenant_id=5, email="mentor@example.com")
        self.author = SimpleNamespace(id=3, tenant_id=5, email="student@example.com")

    async def get_by_id_in_tenant(self, user_id: int, tenant_id: int):
        if tenant_id != 5:
            return None
        if user_id == 2:
            return self.user
        if user_id == 3:
            return self.author
        return None


def _build_service() -> tuple[CommunityService, _CommunityRepository]:
    service = CommunityService(session=SimpleNamespace())
    repository = _CommunityRepository()
    service.repository = repository
    service.user_repository = _UserRepository()
    return service, repository


def test_delete_community_raises_not_found_for_wrong_tenant():
    async def _run():
        service, _ = _build_service()

        with pytest.raises(NotFoundError):
            await service.delete_community(tenant_id=999, community_id=7)

    asyncio.run(_run())


def test_revoke_badge_raises_not_found_for_wrong_tenant():
    async def _run():
        service, _ = _build_service()

        with pytest.raises(NotFoundError):
            await service.revoke_badge(tenant_id=999, badge_id=4)

    asyncio.run(_run())


def test_create_thread_requires_membership_for_student():
    async def _run():
        service, _ = _build_service()

        with pytest.raises(UnauthorizedError):
            await service.create_thread(
                tenant_id=5,
                community_id=7,
                author_user_id=3,
                author_role="student",
                title="Need help",
                body="How do I revise?",
            )

    asyncio.run(_run())


def test_join_community_rejects_duplicate_membership():
    async def _run():
        service, repository = _build_service()
        repository.member = SimpleNamespace(id=10, tenant_id=5, community_id=7, user_id=3, role="student")

        with pytest.raises(ConflictError):
            await service.join_community(tenant_id=5, community_id=7, user_id=3, role="student")

    asyncio.run(_run())


def test_resolve_thread_raises_not_found_for_wrong_tenant():
    async def _run():
        service, _ = _build_service()

        with pytest.raises(NotFoundError):
            await service.resolve_thread(tenant_id=999, thread_id=11, is_resolved=True)

    asyncio.run(_run())
