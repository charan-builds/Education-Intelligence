from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.user_service import UserService
from app.core.dependencies import get_current_user, get_pagination_params, require_roles
from app.infrastructure.database import get_db_session
from app.schemas.common_schema import PaginationParams
from app.schemas.user_schema import UserCreateRequest, UserPageResponse, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse)
async def create_user(
    payload: UserCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("super_admin", "admin")),
):
    service = UserService(db)
    return await service.create_user(
        tenant_id=current_user.tenant_id,
        email=payload.email,
        password=payload.password,
        role=payload.role,
    )


@router.get("", response_model=UserPageResponse)
async def list_users(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination_params),
):
    return await UserService(db).list_users_page(
        tenant_id=current_user.tenant_id,
        limit=pagination.limit,
        offset=pagination.offset,
        cursor=pagination.cursor,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    return current_user
