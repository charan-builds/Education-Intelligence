from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import User, UserRole
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.user_tenant_role_repository import UserTenantRoleRepository
from app.infrastructure.repositories.tenant_scoping import user_belongs_to_tenant, user_has_tenant_role


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.user_tenant_role_repository = UserTenantRoleRepository(session)

    async def create(self, tenant_id: int, email: str, password_hash: str, role: UserRole, created_at):
        user = User(
            tenant_id=tenant_id,
            email=email,
            password_hash=password_hash,
            role=role,
            created_at=created_at,
        )
        self.session.add(user)
        await self.session.flush()
        await self.user_tenant_role_repository.ensure_membership(user_id=int(user.id), tenant_id=tenant_id, role=role)
        return user

    async def get_by_email(self, email: str, *, tenant_id: int | None = None) -> User | None:
        stmt = select(User).where(User.email == email)
        if tenant_id is not None:
            stmt = stmt.where(user_belongs_to_tenant(User, tenant_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_id_in_tenant(self, user_id: int, tenant_id: int) -> User | None:
        result = await self.session.execute(
            select(User)
            .where(
                User.id == user_id,
                user_belongs_to_tenant(User, tenant_id),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_ids_in_tenant(self, user_ids: list[int], tenant_id: int) -> list[User]:
        if not user_ids:
            return []
        result = await self.session.execute(
            select(User)
            .where(
                User.id.in_(user_ids),
                user_belongs_to_tenant(User, tenant_id),
            )
        )
        return list(result.scalars().all())

    async def get_by_email_in_tenant(self, email: str, tenant_id: int) -> User | None:
        return await self.get_by_email(email, tenant_id=tenant_id)

    async def list_by_tenant(
        self,
        tenant_id: int,
        limit: int,
        offset: int,
        cursor_id: int | None = None,
    ) -> list[User]:
        stmt = (
            select(User)
            .where(user_belongs_to_tenant(User, tenant_id))
            .order_by(User.id)
        )
        if cursor_id is not None:
            stmt = stmt.where(User.id > cursor_id).limit(limit)
        else:
            stmt = self.apply_pagination(stmt, limit=limit, offset=offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_tenant_and_roles(
        self,
        tenant_id: int,
        roles: list[UserRole],
        limit: int = 50,
    ) -> list[User]:
        if not roles:
            return []
        result = await self.session.execute(
            select(User)
            .where(
                user_has_tenant_role(User, tenant_id, *[role.value for role in roles]),
            )
            .order_by(User.id.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_tenant(self, tenant_id: int) -> int:
        result = await self.session.execute(
            select(func.count(func.distinct(User.id)))
            .select_from(User)
            .where(user_belongs_to_tenant(User, tenant_id))
        )
        return int(result.scalar_one())
