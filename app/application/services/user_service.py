from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import PasswordValidationError, hash_password, validate_password_strength
from app.core.pagination import decode_cursor, encode_cursor
from app.domain.models.user import User, UserRole
from app.infrastructure.repositories.tenant_repository import TenantRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.application.exceptions import ConflictError, ValidationError


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = UserRepository(session)
        self.tenant_repository = TenantRepository(session)

    async def create_user(self, tenant_id: int, email: str, password: str, role: UserRole) -> User:
        try:
            if role != UserRole.student:
                raise ValidationError("Privileged users must be created through the invite flow")
            tenant = await self.tenant_repository.get_by_id(tenant_id)
            if tenant is None:
                raise ValidationError("Invalid tenant")
            try:
                validate_password_strength(password)
            except PasswordValidationError as exc:
                raise ValidationError(str(exc)) from exc
            existing = await self.repository.get_by_email(email)
            if existing:
                raise ConflictError("Email already registered")
            user = await self.repository.create(
                tenant_id=tenant_id,
                email=email,
                password_hash=hash_password(password),
                role=role,
                created_at=datetime.now(timezone.utc),
            )
            await self.session.commit()
            return user
        except Exception:
            await self.session.rollback()
            raise

    async def list_users(self, tenant_id: int, limit: int, offset: int) -> list[User]:
        return await self.repository.list_by_tenant(tenant_id, limit=limit, offset=offset)

    async def list_users_page(
        self,
        tenant_id: int,
        limit: int,
        offset: int,
        cursor: str | None = None,
    ) -> dict:
        try:
            cursor_id = decode_cursor(cursor) if cursor else None
        except ValueError as exc:
            raise ValidationError("Invalid cursor") from exc
        items = await self.repository.list_by_tenant(
            tenant_id,
            limit=limit,
            offset=offset,
            cursor_id=cursor_id,
        )
        total = await self.repository.count_by_tenant(tenant_id)
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
