from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import decode_cursor, encode_cursor
from app.application.exceptions import ValidationError
from app.domain.models.tenant import Tenant
from app.domain.models.tenant import TenantType
from app.infrastructure.repositories.tenant_repository import TenantRepository


class TenantService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = TenantRepository(session)

    async def create_tenant(self, name: str, tenant_type: TenantType) -> Tenant:
        try:
            tenant = await self.repository.create(
                name=name,
                tenant_type=tenant_type,
                created_at=datetime.now(timezone.utc),
            )
            await self.session.commit()
            return tenant
        except Exception:
            await self.session.rollback()
            raise

    async def list_tenants(self, limit: int, offset: int) -> list[Tenant]:
        return await self.repository.list_all(limit=limit, offset=offset)

    async def list_tenants_page(self, limit: int, offset: int, cursor: str | None = None) -> dict:
        try:
            cursor_id = decode_cursor(cursor) if cursor else None
        except ValueError as exc:
            raise ValidationError("Invalid cursor") from exc
        items = await self.repository.list_all(limit=limit, offset=offset, cursor_id=cursor_id)
        total = await self.repository.count_all()
        next_cursor = encode_cursor(items[-1].id) if items and len(items) == limit else None
        next_offset = offset + limit if (offset + limit) < total else None
        return {
            "items": items,
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "next_cursor": next_cursor,
            },
        }
