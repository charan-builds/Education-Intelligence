from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.user_service import UserService
from app.core.dependencies import get_current_user, get_pagination_params, require_roles
from app.infrastructure.database import get_db_session
from app.schemas.common_schema import PaginationParams
from app.schemas.user_schema import UserCreateRequest, UserPageResponse, UserProfileUpdateRequest, UserResponse

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
    current_user=Depends(require_roles("admin", "super_admin")),
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
    return {
        "id": int(current_user.user.id),
        "tenant_id": int(current_user.tenant_id),
        "email": current_user.user.email,
        "role": current_user.role,
        "display_name": current_user.user.display_name,
        "avatar_url": current_user.user.avatar_url,
        "preferences": current_user.user.preferences_json or {},
        "mfa_enabled": bool(getattr(current_user.user, "mfa_enabled", False)),
        "email_verified_at": getattr(current_user.user, "email_verified_at", None),
        "created_at": current_user.user.created_at,
    }


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserProfileUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    user = await UserService(db).update_profile(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        display_name=payload.display_name,
        avatar_url=payload.avatar_url,
        preferences=payload.preferences,
    )
    return {
        "id": int(user.id),
        "tenant_id": int(current_user.tenant_id),
        "email": user.email,
        "role": current_user.role,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "preferences": user.preferences_json or {},
        "mfa_enabled": bool(getattr(user, "mfa_enabled", False)),
        "email_verified_at": getattr(user, "email_verified_at", None),
        "created_at": user.created_at,
    }
