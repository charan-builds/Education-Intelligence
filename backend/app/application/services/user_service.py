from datetime import datetime, timezone
import re
from urllib.parse import urlparse

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
            existing = await self.repository.get_by_email(email, tenant_id=tenant_id)
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

    async def get_profile(self, *, user_id: int, tenant_id: int) -> User:
        user = await self.repository.get_by_id_in_tenant(user_id, tenant_id)
        if user is None:
            raise ValidationError("User not found")
        return user

    async def update_profile(
        self,
        *,
        user_id: int,
        tenant_id: int,
        full_name: str | None,
        display_name: str | None,
        phone_number: str | None,
        linkedin_url: str | None,
        avatar_url: str | None,
        preferences: dict[str, object],
        organization_name: str | None = None,
        college_name: str | None = None,
    ) -> User:
        try:
            user = await self.get_profile(user_id=user_id, tenant_id=tenant_id)
            normalized_full_name = (full_name or "").strip() or None
            user.display_name = (display_name or "").strip() or None
            user.full_name = normalized_full_name
            user.phone_number = self._normalize_phone_number(phone_number) if phone_number else None
            user.linkedin_url = self._normalize_linkedin_url(linkedin_url) if linkedin_url else None
            resolved_organization_name = organization_name if organization_name is not None else college_name
            user.college_name = (resolved_organization_name or "").strip() or None
            user.avatar_url = (avatar_url or "").strip() or None
            user.preferences_json = preferences or {}
            if normalized_full_name and not user.display_name:
                user.display_name = normalized_full_name
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except Exception:
            await self.session.rollback()
            raise

    async def complete_profile(
        self,
        *,
        user_id: int,
        tenant_id: int,
        full_name: str,
        phone_number: str,
        linkedin_url: str,
        organization_name: str | None = None,
        college_name: str | None = None,
    ) -> User:
        try:
            user = await self.get_profile(user_id=user_id, tenant_id=tenant_id)
            normalized_full_name = full_name.strip()
            if not normalized_full_name:
                raise ValidationError("Full name is required")
            user.full_name = normalized_full_name
            user.display_name = normalized_full_name
            user.phone_number = self._normalize_phone_number(phone_number)
            user.linkedin_url = self._normalize_linkedin_url(linkedin_url)
            resolved_organization_name = organization_name if organization_name is not None else college_name
            user.college_name = (resolved_organization_name or "").strip() or None
            user.is_profile_completed = True
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except Exception:
            await self.session.rollback()
            raise

    @staticmethod
    def _normalize_phone_number(phone_number: str) -> str:
        compact = re.sub(r"[^\d+]", "", phone_number.strip())
        if not re.fullmatch(r"\+?[1-9]\d{7,14}", compact):
            raise ValidationError("Invalid phone number")
        return compact

    @staticmethod
    def _normalize_linkedin_url(linkedin_url: str) -> str:
        normalized = linkedin_url.strip()
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or "linkedin.com" not in parsed.netloc.lower():
            raise ValidationError("Invalid LinkedIn URL")
        return normalized

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
