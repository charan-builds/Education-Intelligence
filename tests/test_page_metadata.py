import asyncio
from dataclasses import dataclass

from app.application.services.tenant_service import TenantService
from app.application.services.user_service import UserService


class _Session:
    pass


@dataclass
class _Entity:
    id: int


def test_tenant_page_metadata_next_offset():
    class _Repo:
        async def list_all(self, limit, offset, cursor_id=None):
            return [_Entity(id=1), _Entity(id=2)]

        async def count_all(self):
            return 5

    async def _run():
        service = TenantService(_Session())
        service.repository = _Repo()
        page = await service.list_tenants_page(limit=2, offset=0)
        assert page["meta"]["total"] == 5
        assert page["meta"]["next_offset"] == 2
        assert page["meta"]["next_cursor"] is not None

    asyncio.run(_run())


def test_user_page_metadata_no_next_offset_on_last_page():
    class _Repo:
        async def list_by_tenant(self, tenant_id, limit, offset, cursor_id=None):
            return [_Entity(id=3)]

        async def count_by_tenant(self, tenant_id):
            return 3

    async def _run():
        service = UserService(_Session())
        service.repository = _Repo()
        page = await service.list_users_page(tenant_id=1, limit=2, offset=2)
        assert page["meta"]["total"] == 3
        assert page["meta"]["next_offset"] is None
        assert page["meta"]["next_cursor"] is None

    asyncio.run(_run())
