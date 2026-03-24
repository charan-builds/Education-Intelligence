from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import User, UserRole
from app.infrastructure.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

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
        return user

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_id_in_tenant(self, user_id: int, tenant_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id, User.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_by_ids_in_tenant(self, user_ids: list[int], tenant_id: int) -> list[User]:
        if not user_ids:
            return []
        result = await self.session.execute(
            select(User).where(User.id.in_(user_ids), User.tenant_id == tenant_id)
        )
        return list(result.scalars().all())

    async def get_by_email_in_tenant(self, email: str, tenant_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email, User.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: int,
        limit: int,
        offset: int,
        cursor_id: int | None = None,
    ) -> list[User]:
        stmt = select(User).where(User.tenant_id == tenant_id).order_by(User.id)
        if cursor_id is not None:
            stmt = stmt.where(User.id > cursor_id).limit(limit)
        else:
            stmt = self.apply_pagination(stmt, limit=limit, offset=offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_tenant(self, tenant_id: int) -> int:
        result = await self.session.execute(select(func.count(User.id)).where(User.tenant_id == tenant_id))
        return int(result.scalar_one())
