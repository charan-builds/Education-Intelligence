from __future__ import annotations
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.application.services.outbox_service import OutboxService
from app.core.security import (
    ACCESS_TOKEN_COOKIE_NAME,
    AuthenticationError,
    decode_access_token,
    get_token_from_headers_and_cookies,
)
from app.infrastructure.database import open_tenant_session
from app.infrastructure.repositories.community_repository import CommunityRepository
from app.infrastructure.repositories.mentor_chat_repository import MentorChatRepository
from app.realtime.hub import realtime_hub

router = APIRouter(prefix="/realtime", tags=["realtime"])

PRIVILEGED_REALTIME_ROLES = {"teacher", "mentor", "admin", "super_admin"}


async def _can_join_community(*, tenant_id: int, user_id: int, role: str | None, community_id: int) -> bool:
    if role in PRIVILEGED_REALTIME_ROLES:
        return True
    async with open_tenant_session(tenant_id=tenant_id, role=role or "student", actor_user_id=user_id) as session:
        membership = await CommunityRepository(session).get_member(tenant_id, community_id, user_id)
        return membership is not None


async def _can_join_thread(*, tenant_id: int, user_id: int, role: str | None, thread_id: int) -> bool:
    async with open_tenant_session(tenant_id=tenant_id, role=role or "student", actor_user_id=user_id) as session:
        repository = CommunityRepository(session)
        thread = await repository.get_thread(tenant_id, thread_id)
        if thread is None:
            return False
        if role in PRIVILEGED_REALTIME_ROLES:
            return True
        membership = await repository.get_member(tenant_id, int(thread.community_id), user_id)
        return membership is not None


@router.websocket("/ws")
async def realtime_websocket(websocket: WebSocket) -> None:
    token = get_token_from_headers_and_cookies(
        websocket.headers,
        websocket.cookies,
        cookie_name=ACCESS_TOKEN_COOKIE_NAME,
    )
    if not token:
        await websocket.close(code=4401)
        return

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
        actor_tenant_id = int(payload.get("tenant_id", 1))
        tenant_id = actor_tenant_id
        role = str(payload.get("role")) if payload.get("role") is not None else None
        requested_tenant_id = websocket.query_params.get("tenant_id")
        if requested_tenant_id is not None:
            if role != "super_admin":
                await websocket.close(code=4403)
                return
            tenant_id = int(requested_tenant_id)
    except (AuthenticationError, KeyError, ValueError):
        await websocket.close(code=4401)
        return

    await realtime_hub.connect(websocket, tenant_id=tenant_id, user_id=user_id)
    try:
        while True:
            message = await websocket.receive_json()
            if not isinstance(message, dict):
                await websocket.send_json({"type": "error", "detail": "Invalid websocket payload"})
                continue
            action = str(message.get("action") or "")
            if action == "subscribe.community":
                raw_community_id = message.get("community_id")
                if not isinstance(raw_community_id, int) or raw_community_id <= 0:
                    await websocket.send_json({"type": "error", "detail": "Invalid community_id"})
                    continue
                community_id = raw_community_id
                if not await _can_join_community(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    role=role,
                    community_id=community_id,
                ):
                    await websocket.send_json({"type": "error", "detail": "Forbidden community subscription"})
                    continue
                await realtime_hub.subscribe_community(websocket, tenant_id=tenant_id, community_id=community_id)
            elif action == "subscribe.thread":
                raw_thread_id = message.get("thread_id")
                if not isinstance(raw_thread_id, int) or raw_thread_id <= 0:
                    await websocket.send_json({"type": "error", "detail": "Invalid thread_id"})
                    continue
                thread_id = raw_thread_id
                if not await _can_join_thread(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    role=role,
                    thread_id=thread_id,
                ):
                    await websocket.send_json({"type": "error", "detail": "Forbidden thread subscription"})
                    continue
                await realtime_hub.subscribe_thread(websocket, tenant_id=tenant_id, thread_id=thread_id)
            elif action == "community.typing":
                raw_thread_id = message.get("thread_id")
                if not isinstance(raw_thread_id, int) or raw_thread_id <= 0:
                    await websocket.send_json({"type": "error", "detail": "Invalid thread_id"})
                    continue
                thread_id = raw_thread_id
                if not await _can_join_thread(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    role=role,
                    thread_id=thread_id,
                ):
                    await websocket.send_json({"type": "error", "detail": "Forbidden typing event"})
                    continue
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
            elif action == "mentor.chat":
                message_text = str(message.get("message") or "").strip()
                request_id = str(message.get("request_id") or "")
                raw_requested_user_id = message.get("user_id", user_id)
                raw_requested_tenant_id = message.get("tenant_id", tenant_id)
                if not isinstance(raw_requested_user_id, int) or not isinstance(raw_requested_tenant_id, int):
                    await websocket.send_json({"type": "error", "detail": "Invalid chat target"})
                    continue
                requested_user_id = raw_requested_user_id
                requested_tenant_id = raw_requested_tenant_id
                chat_history = message.get("chat_history")
                if not isinstance(chat_history, list):
                    chat_history = []
                chat_history = list(chat_history)
                if not request_id:
                    request_id = f"ws-{user_id}-{uuid4().hex}"
                if not message_text or requested_user_id != user_id or requested_tenant_id != tenant_id:
                    await websocket.send_json({"type": "error", "detail": "Forbidden mentor chat"})
                    continue

                await websocket.send_json({"type": "mentor.response.started", "request_id": request_id})
                async with open_tenant_session(tenant_id=tenant_id, role=role or "student", actor_user_id=user_id) as session:
                    repository = MentorChatRepository(session)
                    # Persist inbound message immediately; if the websocket disconnects mid-stream,
                    # the queued job can still generate the outbound response.
                    await repository.upsert_message(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        request_id=request_id,
                        direction="inbound",
                        channel="websocket",
                        status="received",
                        content=message_text,
                        response_json={"chat_history": chat_history},
                    )
                    await OutboxService(session).add_task_event(
                        task_name="jobs.process_mentor_chat",
                        args=[tenant_id, user_id, request_id],
                        tenant_id=tenant_id,
                        idempotency_key=f"mentor-chat:{tenant_id}:{user_id}:{request_id}",
                    )
                    await session.commit()
    except WebSocketDisconnect:
        await realtime_hub.disconnect(websocket, tenant_id=tenant_id, user_id=user_id)
