from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.feature_flag import FeatureFlag
from app.infrastructure.cache.cache_service import CacheService

SUPPORTED_FEATURE_FLAGS: tuple[str, ...] = (
    "adaptive_testing_enabled",
    "ai_mentor_enabled",
    "ml_recommendation_enabled",
)


def is_supported_feature_flag(flag_name: str) -> bool:
    return flag_name in SUPPORTED_FEATURE_FLAGS


class FeatureFlagService:
    _local_cache: dict[tuple[int, str], tuple[bool, float]] = {}

    def __init__(self, session: AsyncSession, cache_ttl_seconds: int = 60):
        self.session = session
        self.cache_ttl_seconds = cache_ttl_seconds
        self.cache_service = CacheService()

    def _cache_key(self, flag_name: str, tenant_id: int) -> str:
        return f"tenant:{tenant_id}:feature_flag:{flag_name}"

    def _read_local_cache(self, key: tuple[int, str]) -> bool | None:
        cached = self._local_cache.get(key)
        if not cached:
            return None
        value, expires_at = cached
        if time.monotonic() > expires_at:
            self._local_cache.pop(key, None)
            return None
        return value

    def _write_local_cache(self, key: tuple[int, str], value: bool) -> None:
        self._local_cache[key] = (value, time.monotonic() + self.cache_ttl_seconds)

    async def enable_feature(self, flag_name: str, tenant_id: int) -> FeatureFlag:
        result = await self.session.execute(
            select(FeatureFlag).where(
                FeatureFlag.tenant_id == tenant_id,
                FeatureFlag.feature_name == flag_name,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = FeatureFlag(
                tenant_id=tenant_id,
                feature_name=flag_name,
                enabled=True,
                created_at=datetime.now(timezone.utc),
            )
            self.session.add(row)
        else:
            row.enabled = True

        await self.session.commit()
        self._write_local_cache((tenant_id, flag_name), True)
        await self.cache_service.set(self._cache_key(flag_name, tenant_id), {"enabled": True}, ttl=self.cache_ttl_seconds)
        return row

    async def disable_feature(self, flag_name: str, tenant_id: int) -> FeatureFlag:
        result = await self.session.execute(
            select(FeatureFlag).where(
                FeatureFlag.tenant_id == tenant_id,
                FeatureFlag.feature_name == flag_name,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = FeatureFlag(
                tenant_id=tenant_id,
                feature_name=flag_name,
                enabled=False,
                created_at=datetime.now(timezone.utc),
            )
            self.session.add(row)
        else:
            row.enabled = False

        await self.session.commit()
        self._write_local_cache((tenant_id, flag_name), False)
        await self.cache_service.set(self._cache_key(flag_name, tenant_id), {"enabled": False}, ttl=self.cache_ttl_seconds)
        return row

    async def is_enabled(self, flag_name: str, tenant_id: int) -> bool:
        local = self._read_local_cache((tenant_id, flag_name))
        if local is not None:
            return local

        cached = await self.cache_service.get(self._cache_key(flag_name, tenant_id))
        if isinstance(cached, dict) and "enabled" in cached:
            value = bool(cached["enabled"])
            self._write_local_cache((tenant_id, flag_name), value)
            return value

        result = await self.session.execute(
            select(FeatureFlag.enabled).where(
                FeatureFlag.tenant_id == tenant_id,
                FeatureFlag.feature_name == flag_name,
            )
        )
        value = bool(result.scalar_one_or_none() or False)
        self._write_local_cache((tenant_id, flag_name), value)
        await self.cache_service.set(self._cache_key(flag_name, tenant_id), {"enabled": value}, ttl=self.cache_ttl_seconds)
        return value

    async def list_for_tenant(self, tenant_id: int) -> list[FeatureFlag]:
        result = await self.session.execute(
            select(FeatureFlag)
            .where(FeatureFlag.tenant_id == tenant_id)
            .order_by(FeatureFlag.feature_name.asc())
        )
        return list(result.scalars().all())
