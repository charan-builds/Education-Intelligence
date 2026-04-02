from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.core.security import (
    TOKEN_SCOPE_FULL_ACCESS,
    create_access_token,
    create_refresh_token_with_jti,
    decode_access_token,
    decode_refresh_token,
    hash_token_value,
)
from app.domain.models.user import User, UserRole
from app.infrastructure.repositories.refresh_token_repository import RefreshTokenRepository


class TokenService:
    def __init__(self, refresh_token_repository: RefreshTokenRepository):
        self.refresh_token_repository = refresh_token_repository

    @staticmethod
    def refresh_session_expiry() -> datetime:
        settings = get_settings()
        return datetime.now(timezone.utc) + timedelta(minutes=settings.refresh_token_expire_minutes)

    def build_access_token(
        self,
        *,
        user: User,
        tenant_id: int,
        role: UserRole,
        token_version: int,
        session_id: str,
        scope: str = TOKEN_SCOPE_FULL_ACCESS,
    ) -> str:
        payload = {
            "sub": str(user.id),
            "tenant_id": tenant_id,
            "role": role.value,
            "tv": token_version,
            "scope": scope,
        }
        return create_access_token(payload, token_id=session_id)

    async def issue_refresh_token(
        self,
        *,
        user: User,
        tenant_id: int,
        role: UserRole,
        session_id: str,
        token_version: int,
        device: str | None,
        ip_address: str | None,
    ) -> str:
        refresh_token = create_refresh_token_with_jti(
            {
                "sub": str(user.id),
                "tenant_id": tenant_id,
                "role": role.value,
                "tv": token_version,
            },
            token_id=session_id,
        )
        await self.refresh_token_repository.create(
            user_id=int(user.id),
            tenant_id=tenant_id,
            token_hash=hash_token_value(refresh_token),
            token_jti=session_id,
            device_info=device,
            ip_address=ip_address,
            expires_at=self.refresh_session_expiry(),
            metadata={"role": role.value},
        )
        return refresh_token

    @staticmethod
    def decode_refresh(refresh_token: str) -> dict:
        return decode_refresh_token(refresh_token)

    @staticmethod
    def decode_access(access_token: str) -> dict:
        return decode_access_token(access_token)
