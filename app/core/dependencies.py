from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AuthenticationError, decode_access_token
from app.infrastructure.database import get_db_session
from app.infrastructure.repositories.user_repository import UserRepository
from app.schemas.common_schema import PaginationParams

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
        tenant_id = int(payload["tenant_id"])
    except (AuthenticationError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = await UserRepository(db).get_by_id_in_tenant(user_id, tenant_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*roles: str):
    async def _require(user=Depends(get_current_user)):
        if user.role.value not in set(roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _require


def get_pagination_params(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    cursor: str | None = Query(default=None),
) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset, cursor=cursor)
