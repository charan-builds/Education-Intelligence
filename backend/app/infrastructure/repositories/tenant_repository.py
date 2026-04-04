from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.tenant import Tenant, TenantType
from app.infrastructure.repositories.base_repository import BaseRepository


class TenantRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create(self, name: str, tenant_type: TenantType, created_at, *, subdomain: str | None = None):
        tenant = Tenant(name=name, subdomain=subdomain, type=tenant_type, created_at=created_at)
        self.session.add(tenant)
        await self.session.flush()
        return tenant

    async def list_all(self, limit: int, offset: int, cursor_id: int | None = None) -> list[Tenant]:
        stmt = select(Tenant).order_by(Tenant.id)
        if cursor_id is not None:
            stmt = stmt.where(Tenant.id > cursor_id)
            stmt = stmt.limit(limit)
        else:
            stmt = self.apply_pagination(stmt, limit=limit, offset=offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, tenant_id: int) -> Tenant | None:
        result = await self.session.execute(select(Tenant).where(Tenant.id == tenant_id))
        return result.scalar_one_or_none()

    async def get_by_subdomain(self, subdomain: str) -> Tenant | None:
        normalized = subdomain.strip().lower()
        result = await self.session.execute(select(Tenant).where(Tenant.subdomain == normalized))
        return result.scalar_one_or_none()

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(Tenant.id)))
        return int(result.scalar_one())
