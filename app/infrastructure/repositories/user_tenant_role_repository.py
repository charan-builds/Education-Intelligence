from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import UserRole
from app.domain.models.user_tenant_role import UserTenantRole


class UserTenantRoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, *, user_id: int, tenant_id: int, role: UserRole) -> UserTenantRole:
        now = datetime.now(timezone.utc)
        row = UserTenantRole(
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
            created_at=now,
            updated_at=now,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_membership(self, *, user_id: int, tenant_id: int) -> UserTenantRole | None:
        result = await self.session.execute(
            select(UserTenantRole).where(
                UserTenantRole.user_id == user_id,
                UserTenantRole.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def ensure_membership(self, *, user_id: int, tenant_id: int, role: UserRole) -> UserTenantRole:
        existing = await self.get_membership(user_id=user_id, tenant_id=tenant_id)
        if existing is not None:
            if existing.role != role:
                existing.role = role
                existing.updated_at = datetime.now(timezone.utc)
                await self.session.flush()
            return existing
        return await self.create(user_id=user_id, tenant_id=tenant_id, role=role)

    async def list_tenant_ids_for_user(self, *, user_id: int) -> list[int]:
        result = await self.session.execute(
            select(UserTenantRole.tenant_id).where(UserTenantRole.user_id == user_id).order_by(UserTenantRole.tenant_id.asc())
        )
        return [int(value) for value in result.scalars().all()]

    async def count_users_for_tenant(self, *, tenant_id: int) -> int:
        result = await self.session.execute(
            select(func.count(UserTenantRole.id)).where(UserTenantRole.tenant_id == tenant_id)
        )
        return int(result.scalar_one() or 0)
