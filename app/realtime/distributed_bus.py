from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from contextlib import suppress

from app.core.config import get_settings
from app.infrastructure.cache.redis_client import get_redis_client


class DistributedRealtimeBus:
    def __init__(self) -> None:
        settings = get_settings()
        self.redis = get_redis_client()
        self.instance_id = settings.realtime_instance_id
        self.channel_prefix = settings.realtime_pubsub_channel_prefix
        self.presence_ttl_seconds = settings.realtime_presence_ttl_seconds
        self.presence_sync_interval_seconds = settings.realtime_presence_sync_interval_seconds
        self._subscriber_task: asyncio.Task[None] | None = None
        self._presence_task: asyncio.Task[None] | None = None
        self._listener: Callable[[dict], Awaitable[None]] | None = None
        self._closed = False

    def _channel(self, room: str) -> str:
        return f"{self.channel_prefix}:room:{room}"

    def _presence_key(self, tenant_id: int) -> str:
        return f"{self.channel_prefix}:presence:{tenant_id}:{self.instance_id}"

    def _instance_heartbeat_key(self) -> str:
        return f"{self.channel_prefix}:instance:{self.instance_id}"

    async def start(self, listener: Callable[[dict], Awaitable[None]]) -> None:
        if self.redis is None or self._subscriber_task is not None:
            return
        self._listener = listener
        self._closed = False
        self._subscriber_task = asyncio.create_task(self._run_subscriber())
        self._presence_task = asyncio.create_task(self._run_presence_heartbeat())

    async def close(self) -> None:
        self._closed = True
        for task in [self._subscriber_task, self._presence_task]:
            if task is not None:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
        self._subscriber_task = None
        self._presence_task = None

    async def publish(self, *, room: str, event: dict) -> None:
        if self.redis is None:
            return
        payload = json.dumps({"origin": self.instance_id, "room": room, "event": event}, ensure_ascii=True, default=str)
        await self.redis.publish(self._channel(room), payload)

    async def set_presence(self, *, tenant_id: int, user_ids: set[int]) -> None:
        if self.redis is None:
            return
        key = self._presence_key(tenant_id)
        await self.redis.delete(key)
        if user_ids:
            await self.redis.sadd(key, *[str(user_id) for user_id in user_ids])
        await self.redis.expire(key, self.presence_ttl_seconds)

    async def aggregate_presence(self, *, tenant_id: int) -> int:
        if self.redis is None:
            return 0
        pattern = f"{self.channel_prefix}:presence:{tenant_id}:*"
        users: set[str] = set()
        async for key in self.redis.scan_iter(match=pattern):
            members = await self.redis.smembers(key)
            users.update(members)
        return len(users)

    async def _run_subscriber(self) -> None:
        if self.redis is None or self._listener is None:
            return
        pubsub = self.redis.pubsub()
        await pubsub.psubscribe(f"{self.channel_prefix}:room:*")
        try:
            while not self._closed:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if not message or not message.get("data"):
                    await asyncio.sleep(0.05)
                    continue
                data = json.loads(message["data"])
                if data.get("origin") == self.instance_id:
                    continue
                await self._listener(data)
        finally:
            await pubsub.close()

    async def _run_presence_heartbeat(self) -> None:
        if self.redis is None:
            return
        key = self._instance_heartbeat_key()
        while not self._closed:
            await self.redis.set(key, "alive", ex=self.presence_ttl_seconds)
            await asyncio.sleep(self.presence_sync_interval_seconds)


distributed_realtime_bus = DistributedRealtimeBus()
