import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.params import Query as QueryParam
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.feature_flags import FeatureFlagService, SUPPORTED_FEATURE_FLAGS, is_supported_feature_flag
from app.core.logging import get_logger
from app.core.authorization import require_permission
from app.application.services.audit_log_service import AuditLogService
from app.infrastructure.database import get_db_session
from app.presentation.middleware.rate_limiter import limiter, rate_limit_key_by_ip, rate_limit_key_by_user
from app.schemas.feature_flag_schema import (
    FeatureFlagCatalogResponse,
    FeatureFlagPageMeta,
    FeatureFlagPageResponse,
    FeatureFlagResponse,
    FeatureFlagUpdateRequest,
)

router = APIRouter(prefix="/ops/feature-flags", tags=["ops"])
logger = get_logger()


@router.get("", response_model=FeatureFlagPageResponse)
@limiter.limit("30/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("60/minute", key_func=rate_limit_key_by_user)
async def list_feature_flags(
    request: Request,
    tenant_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_permission("feature_flags:read")),
):
    scoped_tenant_id: int
    if current_user.role.value == "super_admin":
        scoped_tenant_id = int(tenant_id if tenant_id is not None else current_user.tenant_id)
    else:
        scoped_tenant_id = int(current_user.tenant_id)

    resolved_limit = limit.default if isinstance(limit, QueryParam) else limit
    resolved_offset = offset.default if isinstance(offset, QueryParam) else offset
    all_items = await FeatureFlagService(db).list_for_tenant(scoped_tenant_id)
    page_items = all_items[resolved_offset : resolved_offset + resolved_limit]
    has_more = resolved_offset + resolved_limit < len(all_items)
    next_offset = resolved_offset + resolved_limit if has_more else None
    payload = FeatureFlagPageResponse(
        items=page_items,
        meta=FeatureFlagPageMeta(
            limit=resolved_limit,
            offset=resolved_offset,
            returned=len(page_items),
            total=len(all_items),
            has_more=has_more,
            next_offset=next_offset,
        ),
    )
    payload_json = json.dumps(payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), default=str)
    etag = f'W/"{hashlib.sha256(payload_json.encode("utf-8")).hexdigest()}"'
    if request.headers.get("if-none-match") == etag:
        return Response(
            status_code=304,
            headers={
                "ETag": etag,
                "Cache-Control": "private, max-age=30",
                "Vary": "Authorization, If-None-Match",
            },
        )
    return JSONResponse(
        content=payload.model_dump(mode="json"),
        headers={
            "ETag": etag,
            "Cache-Control": "private, max-age=30",
            "Vary": "Authorization, If-None-Match",
        },
    )


@router.get("/catalog", response_model=FeatureFlagCatalogResponse)
@limiter.limit("30/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("60/minute", key_func=rate_limit_key_by_user)
async def feature_flag_catalog(
    request: Request,
    current_user=Depends(require_permission("feature_flags:read")),
):
    payload = FeatureFlagCatalogResponse(items=sorted(SUPPORTED_FEATURE_FLAGS))
    payload_json = json.dumps(payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), default=str)
    etag = f'W/"{hashlib.sha256(payload_json.encode("utf-8")).hexdigest()}"'
    if request.headers.get("if-none-match") == etag:
        return Response(
            status_code=304,
            headers={
                "ETag": etag,
                "Cache-Control": "private, max-age=60",
                "Vary": "Authorization, If-None-Match",
            },
        )
    return JSONResponse(
        content=payload.model_dump(mode="json"),
        headers={
            "ETag": etag,
            "Cache-Control": "private, max-age=60",
            "Vary": "Authorization, If-None-Match",
        },
    )


@router.post("/{flag_name}", response_model=FeatureFlagResponse)
@limiter.limit("20/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("40/minute", key_func=rate_limit_key_by_user)
async def update_feature_flag(
    request: Request,
    flag_name: str,
    payload: FeatureFlagUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_permission("feature_flags:update")),
):
    if not is_supported_feature_flag(flag_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported feature flag")

    if current_user.role.value == "super_admin":
        scoped_tenant_id = int(payload.tenant_id if payload.tenant_id is not None else current_user.tenant_id)
    else:
        scoped_tenant_id = int(current_user.tenant_id)

    service = FeatureFlagService(db)
    previous_state = await service.is_enabled(flag_name=flag_name, tenant_id=scoped_tenant_id)
    row = await service.configure_feature(
        flag_name=flag_name,
        tenant_id=scoped_tenant_id,
        enabled=payload.enabled,
        rollout_percentage=payload.rollout_percentage,
        audience_filter=payload.audience_filter,
        experiment_key=payload.experiment_key,
    )

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
                "rollout_percentage": int(row.rollout_percentage),
                "experiment_key": row.experiment_key,
                "path": "/ops/feature-flags/{flag_name}",
                "method": "POST",
            }
        },
    )
    await AuditLogService(db).record(
        tenant_id=scoped_tenant_id,
        user_id=int(current_user.id),
        action="feature_flag_updated",
        resource=flag_name,
        metadata={
            "actor_role": str(current_user.role.value),
            "previous_enabled": previous_state,
            "new_enabled": bool(row.enabled),
            "rollout_percentage": int(row.rollout_percentage),
            "experiment_key": row.experiment_key,
        },
        commit=True,
    )
    return row
