from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.audit_log import AuditLog


class AuditLogService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(
        self,
        *,
        tenant_id: int | None,
        user_id: int | None,
        action: str,
        resource: str,
        metadata: dict | None = None,
        commit: bool = False,
    ) -> AuditLog:
        row = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource=resource,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=True, default=str),
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(row)
        await self.session.flush()
        if commit:
            await self.session.commit()
        return row

    async def list_events(
        self,
        *,
        tenant_id: int | None,
        action: str | None = None,
        resource: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        if tenant_id is not None:
            stmt = stmt.where(AuditLog.tenant_id == tenant_id)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        if resource is not None:
            stmt = stmt.where(AuditLog.resource == resource)
        rows = (await self.session.execute(stmt)).scalars().all()
        return [
            {
                "id": int(row.id),
                "tenant_id": row.tenant_id,
                "user_id": row.user_id,
                "action": row.action,
                "resource": row.resource,
                "timestamp": row.created_at.isoformat(),
                "metadata": json.loads(row.metadata_json or "{}"),
            }
            for row in rows
        ]

    async def export_csv(self, *, tenant_id: int | None, limit: int = 1000) -> tuple[str, bool]:
        items = await self.list_events(tenant_id=tenant_id, limit=limit + 1)
        has_more = len(items) > limit
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "tenant_id", "user_id", "action", "resource", "metadata"])
        for item in items[:limit]:
            writer.writerow(
                [
                    item["timestamp"],
                    item["tenant_id"],
                    item["user_id"],
                    item["action"],
                    item["resource"],
                    json.dumps(item["metadata"], ensure_ascii=True),
                ]
            )
        return output.getvalue(), has_more
