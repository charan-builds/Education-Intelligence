import asyncio

from app.application.services.roadmap_service import RoadmapService
from app.application.services.tenant_service import TenantService
from app.application.services.user_service import UserService


class _Session:
    pass


def test_tenant_service_list_uses_pagination():
    class _Repo:
        async def list_all(self, limit, offset):
            return [{"limit": limit, "offset": offset}]

    async def _run():
        service = TenantService(_Session())
        service.repository = _Repo()
        rows = await service.list_tenants(limit=25, offset=10)
        assert rows == [{"limit": 25, "offset": 10}]

    asyncio.run(_run())


def test_user_service_list_uses_pagination():
    class _Repo:
        async def list_by_tenant(self, tenant_id, limit, offset):
            return [{"tenant_id": tenant_id, "limit": limit, "offset": offset}]

    async def _run():
        service = UserService(_Session())
        service.repository = _Repo()
        rows = await service.list_users(tenant_id=7, limit=50, offset=5)
        assert rows == [{"tenant_id": 7, "limit": 50, "offset": 5}]

    asyncio.run(_run())


def test_roadmap_service_list_uses_pagination():
    class _Repo:
        async def list_user_roadmaps(self, user_id, tenant_id, limit, offset):
            return [{"user_id": user_id, "tenant_id": tenant_id, "limit": limit, "offset": offset}]

    async def _run():
        service = RoadmapService(_Session())
        service.roadmap_repository = _Repo()
        rows = await service.list_for_user(user_id=2, tenant_id=3, limit=20, offset=0)
        assert rows == [{"user_id": 2, "tenant_id": 3, "limit": 20, "offset": 0}]

    asyncio.run(_run())
