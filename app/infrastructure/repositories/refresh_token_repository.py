from __future__ import annotations

from datetime import datetime, timezone
import json

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        user_id: int,
        tenant_id: int,
        token_hash: str,
        token_jti: str,
        device_info: str | None,
        ip_address: str | None,
        expires_at: datetime,
        metadata: dict | None = None,
    ) -> RefreshToken:
        row = RefreshToken(
            user_id=user_id,
            tenant_id=tenant_id,
            token_hash=token_hash,
            token_jti=token_jti,
            device_info=device_info[:255] if device_info else None,
            ip_address=ip_address,
            expires_at=expires_at,
            is_revoked=False,
            created_at=datetime.now(timezone.utc),
            revoked_at=None,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=True, default=str),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_active_by_hash(self, *, token_hash: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked.is_(False),
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        expires_at = row.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            row.expires_at = expires_at
        if expires_at <= datetime.now(timezone.utc):
            return None
        return row

    async def revoke(self, row: RefreshToken) -> None:
        row.is_revoked = True
        row.revoked_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def revoke_for_user(self, *, user_id: int) -> int:
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked.is_(False))
            .values(is_revoked=True, revoked_at=datetime.now(timezone.utc))
        )
        return int(result.rowcount or 0)
