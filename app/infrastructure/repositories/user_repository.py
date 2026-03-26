from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import User, UserRole
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.user_tenant_role_repository import UserTenantRoleRepository
from app.domain.models.user_tenant_role import UserTenantRole


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
            stmt = stmt.outerjoin(UserTenantRole, UserTenantRole.user_id == User.id).where(
                or_(User.tenant_id == tenant_id, UserTenantRole.tenant_id == tenant_id)
            )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_id_in_tenant(self, user_id: int, tenant_id: int) -> User | None:
        result = await self.session.execute(
            select(User)
            .outerjoin(UserTenantRole, UserTenantRole.user_id == User.id)
            .where(
                User.id == user_id,
                or_(User.tenant_id == tenant_id, UserTenantRole.tenant_id == tenant_id),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_ids_in_tenant(self, user_ids: list[int], tenant_id: int) -> list[User]:
        if not user_ids:
            return []
        result = await self.session.execute(
            select(User)
            .outerjoin(UserTenantRole, UserTenantRole.user_id == User.id)
            .where(
                User.id.in_(user_ids),
                or_(User.tenant_id == tenant_id, UserTenantRole.tenant_id == tenant_id),
            )
        )
        return list(result.scalars().unique().all())

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
            .outerjoin(UserTenantRole, UserTenantRole.user_id == User.id)
            .where(or_(User.tenant_id == tenant_id, UserTenantRole.tenant_id == tenant_id))
            .order_by(User.id)
        )
        if cursor_id is not None:
            stmt = stmt.where(User.id > cursor_id).limit(limit)
        else:
            stmt = self.apply_pagination(stmt, limit=limit, offset=offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

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
            .outerjoin(UserTenantRole, UserTenantRole.user_id == User.id)
            .where(
                or_(User.tenant_id == tenant_id, UserTenantRole.tenant_id == tenant_id),
                or_(User.role.in_(roles), UserTenantRole.role.in_(roles)),
            )
            .order_by(User.id.asc())
            .limit(limit)
        )
        return list(result.scalars().unique().all())

    async def count_by_tenant(self, tenant_id: int) -> int:
        result = await self.session.execute(
            select(func.count(func.distinct(User.id)))
            .select_from(User)
            .outerjoin(UserTenantRole, UserTenantRole.user_id == User.id)
            .where(or_(User.tenant_id == tenant_id, UserTenantRole.tenant_id == tenant_id))
        )
        return int(result.scalar_one())
