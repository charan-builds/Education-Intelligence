from fastapi import Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_context import AuthContext, validate_tenant_membership
from app.core.security import (
    ACCESS_TOKEN_COOKIE_NAME,
    AuthenticationError,
    TOKEN_SCOPE_FULL_ACCESS,
    decode_access_token,
    get_token_from_headers_and_cookies,
)
from app.infrastructure.database import get_db_session
from app.infrastructure.repositories.user_tenant_role_repository import UserTenantRoleRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.session_repository import SessionRepository
from app.infrastructure.repositories.token_blacklist_repository import TokenBlacklistRepository
from app.schemas.common_schema import PaginationParams


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    token: str | None = None,
 ) -> AuthContext:
    if token is None:
        token = get_token_from_headers_and_cookies(
        request.headers,
        request.cookies,
        cookie_name=ACCESS_TOKEN_COOKIE_NAME,
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
        actor_tenant_id = int(payload["tenant_id"])
        session_id = str(payload["jti"])
        token_version = int(payload.get("tv", 0))
        token_scope = str(payload.get("scope", TOKEN_SCOPE_FULL_ACCESS))
    except (AuthenticationError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    session_repository = SessionRepository(db)
    blacklist_repository = TokenBlacklistRepository(db)
    if await blacklist_repository.is_blacklisted(token_jti=session_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    active_session = await session_repository.get_active(session_id=session_id)
    if (
        active_session is None
        or int(active_session.user_id) != user_id
        or int(active_session.tenant_id) != actor_tenant_id
        or int(active_session.token_version) != token_version
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is no longer active")

    user_repository = UserRepository(db)
    membership_repository = UserTenantRoleRepository(db)
    user = await user_repository.get_by_id_in_tenant(user_id, actor_tenant_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    membership = await membership_repository.get_membership(user_id=user_id, tenant_id=actor_tenant_id)
    membership_role = membership.role if membership is not None else user.role

    effective_tenant_id = actor_tenant_id

    request.state.actor_tenant_id = actor_tenant_id
    request.state.tenant_id = effective_tenant_id
    request.state.tenant_role = membership_role.value if hasattr(membership_role, "value") else str(membership_role)
    request.state.actor_user_id = int(user.id)
    auth_context = AuthContext(
        user=user,
        actor_user_id=int(user.id),
        actor_tenant_id=actor_tenant_id,
        effective_tenant_id=effective_tenant_id,
        membership_role=membership_role,
        token_scope=token_scope,
    )
    request.state.user = auth_context
    request.state.auth_context = auth_context
    return auth_context


async def require_authenticated_user(current_user=Depends(get_current_user)) -> AuthContext:
    return current_user


async def require_email_verified(current_user=Depends(get_current_user)) -> AuthContext:
    if not bool(getattr(current_user.user, "is_email_verified", False) or getattr(current_user.user, "email_verified_at", None)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    return current_user


async def require_profile_completed(current_user=Depends(require_email_verified)) -> AuthContext:
    if not bool(getattr(current_user.user, "is_profile_completed", False)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Profile incomplete")
    if getattr(current_user, "token_scope", TOKEN_SCOPE_FULL_ACCESS) != TOKEN_SCOPE_FULL_ACCESS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Full access required")
    return current_user


def require_roles(*roles: str):
    async def _require(user=Depends(get_current_user)):
        if user.role.value not in set(roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _require


async def require_tenant_membership(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> AuthContext:
    await validate_tenant_membership(user_id=current_user.id, tenant_id=current_user.tenant_id, db_session=db)
    return current_user


def get_request_tenant_id(request: Request) -> int:
    tenant_id = getattr(request.state, "tenant_id", None)
    if isinstance(tenant_id, int):
        return tenant_id
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant context missing")


def get_pagination_params(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    cursor: str | None = Query(default=None),
) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset, cursor=cursor)
