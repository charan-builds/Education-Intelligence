from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.audit_log import AuditLog


class AuditLogService:
    def __init__(self, session: AsyncSession | None = None, *, log_file_path: str | None = None):
        self.session = session
        self.log_file_path = log_file_path

    @staticmethod
    def _parse_timestamp(value: object) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _iter_json_lines(self) -> list[dict]:
        if not self.log_file_path:
            return []
        path = Path(self.log_file_path)
        if not path.exists():
            return []
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return []
        items: list[dict] = []
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                items.append(payload)
        return items

    def list_feature_flag_events(
        self,
        *,
        tenant_id: int | None,
        limit: int = 100,
        offset: int = 0,
        since: datetime | None = None,
        until: datetime | None = None,
        feature_name: str | None = None,
        order: str = "desc",
    ) -> list[dict]:
        normalized_order = (order or "desc").strip().lower()
        if normalized_order not in {"asc", "desc"}:
            normalized_order = "desc"
        normalized_feature = feature_name.strip() if isinstance(feature_name, str) and feature_name.strip() else None

        events: list[dict] = []
        for row in self._iter_json_lines():
            if row.get("event") != "feature_flag_updated":
                continue
            target_tenant = row.get("target_tenant_id")
            if tenant_id is not None and int(target_tenant or 0) != int(tenant_id):
                continue
            if normalized_feature is not None and str(row.get("feature_name") or "") != normalized_feature:
                continue
            ts = self._parse_timestamp(row.get("timestamp"))
            if since is not None and ts is not None and ts < since.astimezone(timezone.utc):
                continue
            if until is not None and ts is not None and ts > until.astimezone(timezone.utc):
                continue
            events.append(
                {
                    "timestamp": ts.isoformat() if ts is not None else None,
                    "actor_user_id": row.get("actor_user_id"),
                    "actor_role": row.get("actor_role"),
                    "target_tenant_id": row.get("target_tenant_id"),
                    "feature_name": row.get("feature_name"),
                    "previous_enabled": row.get("previous_enabled"),
                    "new_enabled": row.get("new_enabled"),
                    "path": row.get("path"),
                    "method": row.get("method"),
                }
            )

        def _sort_key(item: dict) -> tuple:
            # Sort primarily by timestamp, but keep stable ordering for missing timestamps.
            ts_value = item.get("timestamp") or ""
            return (ts_value, str(item.get("feature_name") or ""))

        events.sort(key=_sort_key, reverse=(normalized_order == "desc"))
        if offset < 0:
            offset = 0
        if limit < 0:
            limit = 0
        return events[offset : offset + limit]

    def list_feature_names(self, *, tenant_id: int | None) -> list[str]:
        names: set[str] = set()
        for item in self.list_feature_flag_events(tenant_id=tenant_id, limit=10_000):
            name = item.get("feature_name")
            if isinstance(name, str) and name:
                names.add(name)
        return sorted(names)

    def export_feature_flag_events_csv(self, *, tenant_id: int | None, limit: int = 1000) -> tuple[str, bool]:
        items = self.list_feature_flag_events(tenant_id=tenant_id, limit=limit + 1)
        has_more = len(items) > limit
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "timestamp",
                "actor_user_id",
                "actor_role",
                "target_tenant_id",
                "feature_name",
                "previous_enabled",
                "new_enabled",
                "path",
                "method",
            ]
        )
        for item in items[:limit]:
            writer.writerow(
                [
                    item.get("timestamp"),
                    item.get("actor_user_id"),
                    item.get("actor_role"),
                    item.get("target_tenant_id"),
                    item.get("feature_name"),
                    item.get("previous_enabled"),
                    item.get("new_enabled"),
                    item.get("path"),
                    item.get("method"),
                ]
            )
        return output.getvalue(), has_more

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
        if self.session is None:
            raise RuntimeError("AuditLogService requires a database session for record()")
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
        if self.session is None:
            raise RuntimeError("AuditLogService requires a database session for list_events()")
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
        if self.session is None:
            raise RuntimeError("AuditLogService requires a database session for export_csv()")
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
