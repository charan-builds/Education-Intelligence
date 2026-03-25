from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.feature_flag import FeatureFlag
from app.infrastructure.cache.cache_service import CacheService

SUPPORTED_FEATURE_FLAGS: tuple[str, ...] = (
    "adaptive_testing_enabled",
    "ai_mentor_enabled",
    "ai_question_generation_enabled",
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

    def _list_cache_key(self, tenant_id: int) -> str:
        return f"tenant:{tenant_id}:feature_flags:list"

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
        return await self.configure_feature(flag_name=flag_name, tenant_id=tenant_id, enabled=True)

    async def disable_feature(self, flag_name: str, tenant_id: int) -> FeatureFlag:
        return await self.configure_feature(flag_name=flag_name, tenant_id=tenant_id, enabled=False)

    async def configure_feature(
        self,
        *,
        flag_name: str,
        tenant_id: int,
        enabled: bool,
        rollout_percentage: int = 100,
        audience_filter: dict | None = None,
        experiment_key: str | None = None,
    ) -> FeatureFlag:
        result = await self.session.execute(
            select(FeatureFlag).where(
                FeatureFlag.tenant_id == tenant_id,
                FeatureFlag.feature_name == flag_name,
            )
        )
        row = result.scalar_one_or_none()
        rollout_percentage = max(0, min(100, int(rollout_percentage)))
        audience_filter_json = json.dumps(audience_filter or {}, ensure_ascii=True, sort_keys=True)
        if row is None:
            row = FeatureFlag(
                tenant_id=tenant_id,
                feature_name=flag_name,
                enabled=enabled,
                rollout_percentage=rollout_percentage,
                audience_filter_json=audience_filter_json,
                experiment_key=experiment_key,
                created_at=datetime.now(timezone.utc),
            )
            self.session.add(row)
        else:
            row.enabled = enabled
            row.rollout_percentage = rollout_percentage
            row.audience_filter_json = audience_filter_json
            row.experiment_key = experiment_key

        await self.session.commit()
        self._write_local_cache((tenant_id, flag_name), bool(enabled))
        await self.cache_service.set(
            self._cache_key(flag_name, tenant_id),
            {
                "enabled": bool(enabled),
                "rollout_percentage": rollout_percentage,
                "audience_filter_json": audience_filter_json,
                "experiment_key": experiment_key,
            },
            ttl=self.cache_ttl_seconds,
        )
        await self.cache_service.delete(self._list_cache_key(tenant_id))
        return row

    async def is_enabled(
        self,
        flag_name: str,
        tenant_id: int,
        *,
        subject_id: int | None = None,
        attributes: dict | None = None,
    ) -> bool:
        local = self._read_local_cache((tenant_id, flag_name))
        if local is not None and subject_id is None and not attributes:
            return local

        cached = await self.cache_service.get(self._cache_key(flag_name, tenant_id))
        if isinstance(cached, dict) and "enabled" in cached:
            value = self._evaluate_cached_flag(cached, subject_id=subject_id, attributes=attributes or {})
            self._write_local_cache((tenant_id, flag_name), value)
            return value

        result = await self.session.execute(
            select(FeatureFlag).where(
                FeatureFlag.tenant_id == tenant_id,
                FeatureFlag.feature_name == flag_name,
            )
        )
        row = result.scalar_one_or_none()
        cached_payload = {
            "enabled": bool(row.enabled) if row is not None else False,
            "rollout_percentage": int(row.rollout_percentage) if row is not None else 0,
            "audience_filter_json": row.audience_filter_json if row is not None else "{}",
            "experiment_key": row.experiment_key if row is not None else None,
        }
        value = self._evaluate_cached_flag(cached_payload, subject_id=subject_id, attributes=attributes or {})
        self._write_local_cache((tenant_id, flag_name), value)
        await self.cache_service.set(self._cache_key(flag_name, tenant_id), cached_payload, ttl=self.cache_ttl_seconds)
        return value

    @staticmethod
    def _evaluate_cached_flag(cached: dict, *, subject_id: int | None, attributes: dict) -> bool:
        if not bool(cached.get("enabled")):
            return False
        filters = json.loads(str(cached.get("audience_filter_json") or "{}"))
        for key, expected in filters.items():
            if attributes.get(key) != expected:
                return False
        rollout_percentage = max(0, min(100, int(cached.get("rollout_percentage", 100))))
        if rollout_percentage >= 100 or subject_id is None:
            return True
        bucket = int(hashlib.sha256(str(subject_id).encode("utf-8")).hexdigest()[:8], 16) % 100
        return bucket < rollout_percentage

    async def list_for_tenant(self, tenant_id: int) -> list[FeatureFlag]:
        cached = await self.cache_service.get(self._list_cache_key(tenant_id))
        if isinstance(cached, list):
            return [
                FeatureFlag(
                    id=item["id"],
                    tenant_id=item["tenant_id"],
                    feature_name=item["feature_name"],
                    enabled=item["enabled"],
                    rollout_percentage=item.get("rollout_percentage", 100),
                    audience_filter_json=item.get("audience_filter_json", "{}"),
                    experiment_key=item.get("experiment_key"),
                    created_at=datetime.fromisoformat(item["created_at"]),
                )
                for item in cached
            ]
        result = await self.session.execute(
            select(FeatureFlag)
            .where(FeatureFlag.tenant_id == tenant_id)
            .order_by(FeatureFlag.feature_name.asc())
        )
        rows = list(result.scalars().all())
        await self.cache_service.set(
            self._list_cache_key(tenant_id),
            [
                {
                    "id": row.id,
                    "tenant_id": row.tenant_id,
                    "feature_name": row.feature_name,
                    "enabled": row.enabled,
                    "rollout_percentage": row.rollout_percentage,
                    "audience_filter_json": row.audience_filter_json,
                    "experiment_key": row.experiment_key,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ],
            ttl=self.cache_ttl_seconds,
        )
        return rows
