from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import WebSocket


class RealtimeHub:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._tenant_presence: dict[int, set[int]] = defaultdict(set)
        self._lock = asyncio.Lock()

    @staticmethod
    def _tenant_room(tenant_id: int) -> str:
        return f"tenant:{tenant_id}"

    @staticmethod
    def _user_room(tenant_id: int, user_id: int) -> str:
        return f"user:{tenant_id}:{user_id}"

    @staticmethod
    def _community_room(tenant_id: int, community_id: int) -> str:
        return f"community:{tenant_id}:{community_id}"

    @staticmethod
    def _thread_room(tenant_id: int, thread_id: int) -> str:
        return f"thread:{tenant_id}:{thread_id}"

    async def connect(self, websocket: WebSocket, *, tenant_id: int, user_id: int) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[self._tenant_room(tenant_id)].add(websocket)
            self._connections[self._user_room(tenant_id, user_id)].add(websocket)
            self._tenant_presence[tenant_id].add(user_id)
        await self.broadcast_presence(tenant_id)

    async def disconnect(self, websocket: WebSocket, *, tenant_id: int, user_id: int) -> None:
        async with self._lock:
            for sockets in self._connections.values():
                sockets.discard(websocket)
            still_connected = any(websocket in sockets for sockets in self._connections.values())
            if not still_connected:
                user_room = self._user_room(tenant_id, user_id)
                remaining_for_user = self._connections.get(user_room, set())
                if len(remaining_for_user) == 0:
                    self._tenant_presence[tenant_id].discard(user_id)
        await self.broadcast_presence(tenant_id)

    async def subscribe_community(self, websocket: WebSocket, *, tenant_id: int, community_id: int) -> None:
        async with self._lock:
            self._connections[self._community_room(tenant_id, community_id)].add(websocket)

    async def subscribe_thread(self, websocket: WebSocket, *, tenant_id: int, thread_id: int) -> None:
        async with self._lock:
            self._connections[self._thread_room(tenant_id, thread_id)].add(websocket)

    async def send_user(self, tenant_id: int, user_id: int, event: dict) -> None:
        await self._broadcast(self._user_room(tenant_id, user_id), event)

    async def send_thread(self, tenant_id: int, thread_id: int, event: dict) -> None:
        await self._broadcast(self._thread_room(tenant_id, thread_id), event)

    async def send_community(self, tenant_id: int, community_id: int, event: dict) -> None:
        await self._broadcast(self._community_room(tenant_id, community_id), event)

    async def send_tenant(self, tenant_id: int, event: dict) -> None:
        await self._broadcast(self._tenant_room(tenant_id), event)

    async def broadcast_presence(self, tenant_id: int) -> None:
        await self.send_tenant(
            tenant_id,
            {
                "type": "presence.snapshot",
                "tenant_id": tenant_id,
                "active_users": len(self._tenant_presence.get(tenant_id, set())),
                "sent_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def _broadcast(self, room: str, event: dict) -> None:
        async with self._lock:
            sockets = list(self._connections.get(room, set()))
        disconnected: list[WebSocket] = []
        for websocket in sockets:
            try:
                await websocket.send_json(event)
            except Exception:
                disconnected.append(websocket)

        if disconnected:
            async with self._lock:
                for socket in disconnected:
                    for room_sockets in self._connections.values():
                        room_sockets.discard(socket)


realtime_hub = RealtimeHub()
