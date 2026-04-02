from __future__ import annotations

from datetime import datetime, timezone
import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.auth_log import AuthLog


class AuthLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        tenant_id: int | None,
        user_id: int | None,
        email: str | None,
        event_type: str,
        status: str,
        ip_address: str | None,
        user_agent: str | None,
        detail: str | None = None,
        metadata: dict | None = None,
    ) -> AuthLog:
        row = AuthLog(
            tenant_id=tenant_id,
            user_id=user_id,
            email=email,
            event_type=event_type,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else None,
            detail=detail,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=True, default=str),
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(row)
        await self.session.flush()
        return row
