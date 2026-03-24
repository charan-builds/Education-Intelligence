from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AuthenticationError, decode_access_token
from app.infrastructure.database import get_db_session
from app.infrastructure.repositories.user_repository import UserRepository
from app.schemas.common_schema import PaginationParams

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
        actor_tenant_id = int(payload.get("tenant_id", get_request_tenant_id(request)))
    except (AuthenticationError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = await UserRepository(db).get_by_id_in_tenant(user_id, actor_tenant_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    effective_tenant_id = actor_tenant_id
    if user.role.value == "super_admin":
        raw_tenant_id = request.headers.get("X-Tenant-ID")
        try:
            if raw_tenant_id is not None:
                effective_tenant_id = int(raw_tenant_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tenant header")
    elif request.headers.get("X-Tenant-ID") is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant override is not allowed")

    request.state.actor_tenant_id = actor_tenant_id
    request.state.tenant_id = effective_tenant_id
    request.state.user = user
    user.tenant_id = effective_tenant_id
    return user


def require_roles(*roles: str):
    async def _require(user=Depends(get_current_user)):
        if user.role.value not in set(roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _require


def get_request_tenant_id(request: Request) -> int:
    tenant_id = getattr(request.state, "tenant_id", None)
    if isinstance(tenant_id, int):
        return tenant_id
    return 1


def get_pagination_params(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    cursor: str | None = Query(default=None),
) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset, cursor=cursor)
