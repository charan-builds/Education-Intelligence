from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.token_blacklist import TokenBlacklist


class TokenBlacklistRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        *,
        token_jti: str,
        user_id: int | None,
        tenant_id: int | None,
        token_type: str,
        expires_at: datetime | None,
    ) -> TokenBlacklist:
        row = TokenBlacklist(
            token_jti=token_jti,
            user_id=user_id,
            tenant_id=tenant_id,
            token_type=token_type,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def is_blacklisted(self, *, token_jti: str) -> bool:
        result = await self.session.execute(select(TokenBlacklist.id).where(TokenBlacklist.token_jti == token_jti))
        return result.scalar_one_or_none() is not None
