from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.feature_flags import FeatureFlagService, SUPPORTED_FEATURE_FLAGS, is_supported_feature_flag
from app.core.logging import get_logger
from app.infrastructure.database import get_db_session
from app.schemas.feature_flag_schema import (
    FeatureFlagCatalogResponse,
    FeatureFlagPageResponse,
    FeatureFlagResponse,
    FeatureFlagUpdateRequest,
)

router = APIRouter(prefix="/ops/feature-flags", tags=["ops"])
logger = get_logger()


@router.get("", response_model=FeatureFlagPageResponse)
async def list_feature_flags(
    tenant_id: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    scoped_tenant_id: int
    if current_user.role.value == "super_admin":
        scoped_tenant_id = int(tenant_id if tenant_id is not None else current_user.tenant_id)
    else:
        scoped_tenant_id = int(current_user.tenant_id)

    items = await FeatureFlagService(db).list_for_tenant(scoped_tenant_id)
    return FeatureFlagPageResponse(items=items)


@router.get("/catalog", response_model=FeatureFlagCatalogResponse)
async def feature_flag_catalog(
    current_user=Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return FeatureFlagCatalogResponse(items=sorted(SUPPORTED_FEATURE_FLAGS))


@router.post("/{flag_name}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    flag_name: str,
    payload: FeatureFlagUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if not is_supported_feature_flag(flag_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported feature flag")

    if current_user.role.value == "super_admin":
        scoped_tenant_id = int(payload.tenant_id if payload.tenant_id is not None else current_user.tenant_id)
    else:
        scoped_tenant_id = int(current_user.tenant_id)

    service = FeatureFlagService(db)
    previous_state = await service.is_enabled(flag_name=flag_name, tenant_id=scoped_tenant_id)
    if payload.enabled:
        row = await service.enable_feature(flag_name=flag_name, tenant_id=scoped_tenant_id)
    else:
        row = await service.disable_feature(flag_name=flag_name, tenant_id=scoped_tenant_id)

    logger.info(
        "feature_flag_updated",
        extra={
            "log_data": {
                "event": "feature_flag_updated",
                "actor_user_id": int(current_user.id) if getattr(current_user, "id", None) is not None else None,
                "actor_role": str(current_user.role.value),
                "target_tenant_id": scoped_tenant_id,
                "feature_name": flag_name,
                "previous_enabled": previous_state,
                "new_enabled": bool(row.enabled),
                "path": "/ops/feature-flags/{flag_name}",
                "method": "POST",
            }
        },
    )
    return row
