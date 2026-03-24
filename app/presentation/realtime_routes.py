from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import AuthenticationError, decode_access_token
from app.realtime.hub import realtime_hub

router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.websocket("/ws")
async def realtime_websocket(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
        tenant_id = int(payload.get("tenant_id", 1))
    except (AuthenticationError, KeyError, ValueError):
        await websocket.close(code=4401)
        return

    await realtime_hub.connect(websocket, tenant_id=tenant_id, user_id=user_id)
    try:
        while True:
            message = await websocket.receive_json()
            action = str(message.get("action") or "")
            if action == "subscribe.community":
                community_id = int(message.get("community_id"))
                await realtime_hub.subscribe_community(websocket, tenant_id=tenant_id, community_id=community_id)
            elif action == "subscribe.thread":
                thread_id = int(message.get("thread_id"))
                await realtime_hub.subscribe_thread(websocket, tenant_id=tenant_id, thread_id=thread_id)
            elif action == "community.typing":
                thread_id = int(message.get("thread_id"))
                await realtime_hub.send_thread(
                    tenant_id,
                    thread_id,
                    {
                        "type": "community.typing",
                        "thread_id": thread_id,
                        "user_id": user_id,
                    },
                )
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await realtime_hub.disconnect(websocket, tenant_id=tenant_id, user_id=user_id)
