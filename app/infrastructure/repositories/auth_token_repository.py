from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.auth_token import AuthToken, AuthTokenPurpose


class AuthTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        user_id: int,
        tenant_id: int,
        purpose: AuthTokenPurpose,
        token_hash: str,
        expires_at: datetime,
        created_at: datetime,
    ) -> AuthToken:
        row = AuthToken(
            user_id=user_id,
            tenant_id=tenant_id,
            purpose=purpose,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=created_at,
            used_at=None,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def invalidate_active_tokens_for_user(self, *, user_id: int, purpose: AuthTokenPurpose) -> int:
        result = await self.session.execute(
            update(AuthToken)
            .where(
                AuthToken.user_id == user_id,
                AuthToken.purpose == purpose,
                AuthToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(timezone.utc))
        )
        return int(result.rowcount or 0)

    async def get_active_by_hash(self, *, token_hash: str, purpose: AuthTokenPurpose) -> AuthToken | None:
        result = await self.session.execute(
            select(AuthToken).where(
                AuthToken.token_hash == token_hash,
                AuthToken.purpose == purpose,
                AuthToken.used_at.is_(None),
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

    async def mark_used(self, row: AuthToken) -> None:
        row.used_at = datetime.now(timezone.utc)
        await self.session.flush()
