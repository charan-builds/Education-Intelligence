from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import WebSocket

from app.core.metrics import websocket_backpressure_total, websocket_connections_active, websocket_messages_total
from app.realtime.distributed_bus import distributed_realtime_bus


class _ConnectionState:
    def __init__(self, websocket: WebSocket, *, tenant_id: int, user_id: int, max_queue_size: int = 200) -> None:
        self.websocket = websocket
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.queue: asyncio.Queue[dict | None] = asyncio.Queue(maxsize=max_queue_size)
        self.sender_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        await self.websocket.accept()
        self.sender_task = asyncio.create_task(self._sender())

    async def _sender(self) -> None:
        while True:
            event = await self.queue.get()
            if event is None:
                return
            try:
                await self.websocket.send_json(event)
                websocket_messages_total.labels(direction="outbound", result="sent").inc()
            except Exception:
                websocket_messages_total.labels(direction="outbound", result="failed").inc()
                return

    async def enqueue(self, event: dict) -> bool:
        if self.queue.full():
            websocket_backpressure_total.labels(tenant_id=str(self.tenant_id)).inc()
            return False
        self.queue.put_nowait(event)
        return True

    async def close(self) -> None:
        if self.sender_task is None:
            return
        try:
            self.queue.put_nowait(None)
        except asyncio.QueueFull:
            pass
        await self.sender_task


class RealtimeHub:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._tenant_presence: dict[int, set[int]] = defaultdict(set)
        self._connection_state: dict[int, _ConnectionState] = {}
        self._websocket_identity: dict[int, tuple[int, int]] = {}
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
        state = _ConnectionState(websocket, tenant_id=tenant_id, user_id=user_id)
        await state.start()
        async with self._lock:
            self._connections[self._tenant_room(tenant_id)].add(websocket)
            self._connections[self._user_room(tenant_id, user_id)].add(websocket)
            self._tenant_presence[tenant_id].add(user_id)
            self._connection_state[id(websocket)] = state
            self._websocket_identity[id(websocket)] = (tenant_id, user_id)
            websocket_connections_active.labels(tenant_id=str(tenant_id)).set(
                len(self._connections[self._tenant_room(tenant_id)])
            )
            await self._sync_presence_locked(tenant_id)
        await self.broadcast_presence(tenant_id)

    async def disconnect(self, websocket: WebSocket, *, tenant_id: int, user_id: int) -> None:
        async with self._lock:
            for sockets in self._connections.values():
                sockets.discard(websocket)
            self._websocket_identity.pop(id(websocket), None)
            state = self._connection_state.pop(id(websocket), None)
            remaining_for_user = self._connections.get(self._user_room(tenant_id, user_id), set())
            if len(remaining_for_user) == 0:
                self._tenant_presence[tenant_id].discard(user_id)
            websocket_connections_active.labels(tenant_id=str(tenant_id)).set(
                len(self._connections.get(self._tenant_room(tenant_id), set()))
            )
            await self._sync_presence_locked(tenant_id)
        if state is not None:
            await state.close()
        await self.broadcast_presence(tenant_id)

    async def subscribe_community(self, websocket: WebSocket, *, tenant_id: int, community_id: int) -> None:
        async with self._lock:
            self._connections[self._community_room(tenant_id, community_id)].add(websocket)

    async def subscribe_thread(self, websocket: WebSocket, *, tenant_id: int, thread_id: int) -> None:
        async with self._lock:
            self._connections[self._thread_room(tenant_id, thread_id)].add(websocket)

    async def send_user(self, tenant_id: int, user_id: int, event: dict) -> None:
        room = self._user_room(tenant_id, user_id)
        await self._broadcast(room, event)
        await distributed_realtime_bus.publish(room=room, event=event)

    async def send_thread(self, tenant_id: int, thread_id: int, event: dict) -> None:
        room = self._thread_room(tenant_id, thread_id)
        await self._broadcast(room, event)
        await distributed_realtime_bus.publish(room=room, event=event)

    async def send_community(self, tenant_id: int, community_id: int, event: dict) -> None:
        room = self._community_room(tenant_id, community_id)
        await self._broadcast(room, event)
        await distributed_realtime_bus.publish(room=room, event=event)

    async def send_tenant(self, tenant_id: int, event: dict) -> None:
        room = self._tenant_room(tenant_id)
        await self._broadcast(room, event)
        await distributed_realtime_bus.publish(room=room, event=event)

    async def broadcast_presence(self, tenant_id: int) -> None:
        active_users = await distributed_realtime_bus.aggregate_presence(tenant_id=tenant_id)
        if active_users <= 0:
            active_users = len(self._tenant_presence.get(tenant_id, set()))
        await self.send_tenant(
            tenant_id,
            {
                "type": "presence.snapshot",
                "tenant_id": tenant_id,
                "active_users": active_users,
                "sent_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def handle_distributed_message(self, payload: dict) -> None:
        room = str(payload.get("room") or "")
        event = payload.get("event") or {}
        if room:
            await self._broadcast(room, event)

    async def _sync_presence_locked(self, tenant_id: int) -> None:
        await distributed_realtime_bus.set_presence(
            tenant_id=tenant_id,
            user_ids=set(self._tenant_presence.get(tenant_id, set())),
        )

    async def _broadcast(self, room: str, event: dict) -> None:
        async with self._lock:
            sockets = list(self._connections.get(room, set()))
            states = {socket: self._connection_state.get(id(socket)) for socket in sockets}
        disconnected: list[tuple[WebSocket, int, int]] = []
        for websocket in sockets:
            state = states.get(websocket)
            if state is None:
                tenant_id, user_id = self._websocket_identity.get(id(websocket), (0, 0))
                disconnected.append((websocket, tenant_id, user_id))
                continue
            if not await state.enqueue(event):
                disconnected.append((websocket, state.tenant_id, state.user_id))

        for websocket, tenant_id, user_id in disconnected:
            if tenant_id > 0:
                await self.disconnect(websocket, tenant_id=tenant_id, user_id=user_id)


realtime_hub = RealtimeHub()
