from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.session import SessionRecord
from app.infrastructure.cache.cache_service import CacheService


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.cache_service = CacheService()

    @staticmethod
    def _cache_key(session_id: str) -> str:
        return f"auth:session:{session_id}"

    @staticmethod
    def _serialize(row: SessionRecord) -> dict:
        return {
            "id": row.id,
            "user_id": int(row.user_id),
            "tenant_id": int(row.tenant_id),
            "token_version": int(row.token_version),
            "device": row.device,
            "expires_at": row.expires_at.isoformat(),
            "revoked": bool(row.revoked),
            "created_at": row.created_at.isoformat(),
            "revoked_at": row.revoked_at.isoformat() if row.revoked_at is not None else None,
        }

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    async def next_token_version_for_user(self, *, user_id: int) -> int:
        result = await self.session.execute(
            select(func.coalesce(func.max(SessionRecord.token_version), 0)).where(SessionRecord.user_id == user_id)
        )
        return int(result.scalar_one() or 0) + 1

    async def create(
        self,
        *,
        session_id: str,
        user_id: int,
        tenant_id: int,
        token_version: int,
        device: str | None,
        expires_at: datetime,
    ) -> SessionRecord:
        row = SessionRecord(
            id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            token_version=token_version,
            device=device[:255] if device else None,
            expires_at=expires_at,
            revoked=False,
            created_at=datetime.now(timezone.utc),
            revoked_at=None,
        )
        self.session.add(row)
        await self.session.flush()
        ttl = max(1, int((self._as_utc(expires_at) - datetime.now(timezone.utc)).total_seconds()))
        await self.cache_service.set(self._cache_key(session_id), self._serialize(row), ttl=ttl)
        return row

    async def get_active(self, *, session_id: str) -> SessionRecord | None:
        cached = await self.cache_service.get(self._cache_key(session_id))
        if isinstance(cached, dict) and not cached.get("revoked"):
            expires_at = self._as_utc(datetime.fromisoformat(str(cached["expires_at"])))
            if expires_at > datetime.now(timezone.utc):
                return SessionRecord(
                    id=str(cached["id"]),
                    user_id=int(cached["user_id"]),
                    tenant_id=int(cached["tenant_id"]),
                    token_version=int(cached["token_version"]),
                    device=cached.get("device"),
                    expires_at=expires_at,
                    revoked=bool(cached.get("revoked", False)),
                    created_at=self._as_utc(datetime.fromisoformat(str(cached["created_at"]))),
                    revoked_at=self._as_utc(datetime.fromisoformat(cached["revoked_at"])) if cached.get("revoked_at") else None,
                )
        result = await self.session.execute(
            select(SessionRecord).where(
                SessionRecord.id == session_id,
                SessionRecord.revoked.is_(False),
            )
        )
        row = result.scalar_one_or_none()
        if row is not None:
            row.expires_at = self._as_utc(row.expires_at)
            row.created_at = self._as_utc(row.created_at)
            if row.revoked_at is not None:
                row.revoked_at = self._as_utc(row.revoked_at)
            ttl = max(1, int((row.expires_at - datetime.now(timezone.utc)).total_seconds()))
            await self.cache_service.set(self._cache_key(session_id), self._serialize(row), ttl=ttl)
        return row

    async def revoke(self, row: SessionRecord) -> None:
        row.revoked = True
        row.revoked_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.cache_service.delete(self._cache_key(row.id))

    async def revoke_by_id(self, *, session_id: str) -> bool:
        row = await self.get_active(session_id=session_id)
        if row is None:
            return False
        await self.revoke(row)
        return True

    async def revoke_for_user(self, *, user_id: int) -> int:
        active_sessions = await self.list_active_for_user(user_id=user_id)
        result = await self.session.execute(
            update(SessionRecord)
            .where(SessionRecord.user_id == user_id, SessionRecord.revoked.is_(False))
            .values(revoked=True, revoked_at=datetime.now(timezone.utc))
        )
        for row in active_sessions:
            await self.cache_service.delete(self._cache_key(row.id))
        return int(result.rowcount or 0)

    async def list_active_for_user(self, *, user_id: int) -> list[SessionRecord]:
        result = await self.session.execute(
            select(SessionRecord)
            .where(SessionRecord.user_id == user_id, SessionRecord.revoked.is_(False))
            .order_by(SessionRecord.created_at.desc())
        )
        return list(result.scalars().all())
