from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.refresh_session import RefreshSession


class RefreshSessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        session_id: str,
        user_id: int,
        device: str | None,
        expires_at: datetime,
    ) -> RefreshSession:
        row = RefreshSession(
            id=session_id,
            user_id=user_id,
            device=device[:255] if device else None,
            expires_at=expires_at,
            revoked=False,
            created_at=datetime.now(timezone.utc),
            revoked_at=None,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_active(self, *, session_id: str) -> RefreshSession | None:
        result = await self.session.execute(
            select(RefreshSession).where(
                RefreshSession.id == session_id,
                RefreshSession.revoked.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, row: RefreshSession) -> None:
        row.revoked = True
        row.revoked_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def revoke_by_id(self, *, session_id: str) -> bool:
        row = await self.get_active(session_id=session_id)
        if row is None:
            return False
        await self.revoke(row)
        return True

    async def revoke_for_user(self, *, user_id: int) -> int:
        result = await self.session.execute(
            update(RefreshSession)
            .where(RefreshSession.user_id == user_id, RefreshSession.revoked.is_(False))
            .values(revoked=True, revoked_at=datetime.now(timezone.utc))
        )
        return int(result.rowcount or 0)

    async def list_active_for_user(self, *, user_id: int) -> list[RefreshSession]:
        result = await self.session.execute(
            select(RefreshSession)
            .where(RefreshSession.user_id == user_id, RefreshSession.revoked.is_(False))
            .order_by(RefreshSession.created_at.desc())
        )
        return list(result.scalars().all())
