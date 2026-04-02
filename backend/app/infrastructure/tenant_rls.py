from __future__ import annotations

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def apply_rls_context(
    session: AsyncSession,
    *,
    tenant_id: int | None,
    role: str | None,
    actor_user_id: int | None = None,
) -> None:
    tenant_value = "" if tenant_id is None else str(int(tenant_id))
    role_value = str(role or "anonymous")
    user_value = "" if actor_user_id is None else str(int(actor_user_id))

    session_info = getattr(session, "info", None)
    if session_info is None:
        session_info = {}
        setattr(session, "info", session_info)
    session_info["tenant_context_explicit"] = True
    session_info["tenant_id"] = None if tenant_id is None else int(tenant_id)
    session_info["tenant_role"] = role_value
    session_info["actor_user_id"] = None if actor_user_id is None else int(actor_user_id)

    await session.execute(text("select set_config('app.current_tenant_id', :value, false)"), {"value": tenant_value})
    await session.execute(text("select set_config('app.current_role', :value, false)"), {"value": role_value})
    await session.execute(text("select set_config('app.current_user_id', :value, false)"), {"value": user_value})


async def apply_request_rls_context(session: AsyncSession, request: Request | None) -> None:
    if request is None:
        await apply_rls_context(session, tenant_id=None, role="anonymous", actor_user_id=None)
        return

    tenant_id = getattr(request.state, "tenant_id", None)
    role = getattr(request.state, "tenant_role", None)
    actor_user_id = getattr(request.state, "actor_user_id", None)
    await apply_rls_context(
        session,
        tenant_id=tenant_id if isinstance(tenant_id, int) else None,
        role=str(role or "anonymous"),
        actor_user_id=actor_user_id if isinstance(actor_user_id, int) else None,
    )
