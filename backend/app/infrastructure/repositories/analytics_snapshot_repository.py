from datetime import datetime
import json

from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domain.models.analytics_snapshot import AnalyticsSnapshot


class AnalyticsSnapshotRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _prune_old_versions(
        self,
        *,
        tenant_id: int | None,
        snapshot_type: str,
        subject_id: int | None,
        latest_version: int,
    ) -> None:
        keep_versions = max(int(get_settings().analytics_snapshot_versions_to_keep), 1)
        cutoff_version = latest_version - keep_versions
        if cutoff_version <= 0:
            return
        await self.session.execute(
            text(
                """
                DELETE FROM analytics_snapshots
                WHERE tenant_id IS NOT DISTINCT FROM :tenant_id
                  AND snapshot_type = :snapshot_type
                  AND subject_id IS NOT DISTINCT FROM :subject_id
                  AND version < :cutoff_version
                """
            ),
            {
                "tenant_id": tenant_id,
                "snapshot_type": snapshot_type,
                "subject_id": subject_id,
                "cutoff_version": cutoff_version,
            },
        )

    async def _acquire_version_lock(
        self,
        *,
        tenant_id: int | None,
        snapshot_type: str,
        subject_id: int | None,
    ) -> None:
        bind = self.session.bind
        dialect = str(bind.dialect.name if bind is not None else "")
        if dialect != "postgresql":
            return

        lock_key = f"analytics_snapshot:{tenant_id or 'global'}:{snapshot_type}:{subject_id or 'global'}"
        # Advisory xact locks are released automatically at transaction end.
        # This serializes version allocation for one logical snapshot identity
        # without taking a broader table lock.
        await self.session.execute(
            text("select pg_advisory_xact_lock(hashtext(:namespace), hashtext(:lock_key))"),
            {"namespace": "analytics_snapshots", "lock_key": lock_key},
        )

    async def _create_snapshot_version_once(
        self,
        *,
        tenant_id: int | None,
        snapshot_type: str,
        subject_id: int | None,
        payload_json: str,
        window_start: datetime,
        window_end: datetime,
        updated_at: datetime,
    ) -> AnalyticsSnapshot:
        await self._acquire_version_lock(
            tenant_id=tenant_id,
            snapshot_type=snapshot_type,
            subject_id=subject_id,
        )
        current_version = await self.session.scalar(
            select(func.max(AnalyticsSnapshot.snapshot_version)).where(
                AnalyticsSnapshot.tenant_id == tenant_id,
                AnalyticsSnapshot.snapshot_type == snapshot_type,
                AnalyticsSnapshot.subject_id == subject_id,
            )
        )
        next_version = int(current_version or 0) + 1
        await self.session.execute(
            update(AnalyticsSnapshot)
            .where(
                AnalyticsSnapshot.tenant_id == tenant_id,
                AnalyticsSnapshot.snapshot_type == snapshot_type,
                AnalyticsSnapshot.subject_id == subject_id,
                AnalyticsSnapshot.is_latest.is_(True),
            )
            .values(is_latest=False)
        )
        payload_data = json.loads(payload_json)
        row = AnalyticsSnapshot(
            tenant_id=tenant_id,
            snapshot_type=snapshot_type,
            subject_id=subject_id,
            payload_json=payload_json,
            data=payload_data,
            window_start=window_start,
            window_end=window_end,
            snapshot_version=next_version,
            version=next_version,
            created_at=updated_at,
            updated_at=updated_at,
            is_latest=True,
        )
        self.session.add(row)
        await self.session.flush()
        await self._prune_old_versions(
            tenant_id=tenant_id,
            snapshot_type=snapshot_type,
            subject_id=subject_id,
            latest_version=next_version,
        )
        return row

    async def create_snapshot_version(
        self,
        *,
        tenant_id: int | None,
        snapshot_type: str,
        subject_id: int | None,
        payload_json: str,
        window_start: datetime,
        window_end: datetime,
        updated_at: datetime,
    ) -> AnalyticsSnapshot:
        for attempt in range(2):
            try:
                if hasattr(self.session, "begin_nested"):
                    async with self.session.begin_nested():
                        return await self._create_snapshot_version_once(
                            tenant_id=tenant_id,
                            snapshot_type=snapshot_type,
                            subject_id=subject_id,
                            payload_json=payload_json,
                            window_start=window_start,
                            window_end=window_end,
                            updated_at=updated_at,
                        )
                return await self._create_snapshot_version_once(
                    tenant_id=tenant_id,
                    snapshot_type=snapshot_type,
                    subject_id=subject_id,
                    payload_json=payload_json,
                    window_start=window_start,
                    window_end=window_end,
                    updated_at=updated_at,
                )
            except IntegrityError:
                if attempt >= 1:
                    raise
        raise RuntimeError("unreachable")

    async def latest_snapshot(
        self,
        *,
        tenant_id: int | None,
        snapshot_type: str,
        subject_id: int | None,
    ) -> AnalyticsSnapshot | None:
        result = await self.session.execute(
            select(AnalyticsSnapshot)
            .where(
                AnalyticsSnapshot.tenant_id == tenant_id,
                AnalyticsSnapshot.snapshot_type == snapshot_type,
                AnalyticsSnapshot.subject_id == subject_id,
                AnalyticsSnapshot.is_latest.is_(True),
            )
            .order_by(AnalyticsSnapshot.snapshot_version.desc(), AnalyticsSnapshot.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
