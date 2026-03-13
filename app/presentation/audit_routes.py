from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from datetime import datetime, timedelta
import hashlib
import json
from fastapi.responses import JSONResponse

from app.application.services.audit_log_service import AuditLogService
from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.presentation.middleware.rate_limiter import limiter, rate_limit_key_by_ip, rate_limit_key_by_user
from app.schemas.audit_schema import AuditFeatureNamesResponse, AuditLogEventsResponse, AuditLogMeta

router = APIRouter(prefix="/ops/audit", tags=["ops"])
settings = get_settings()


@router.get("/feature-flags", response_model=AuditLogEventsResponse)
@limiter.limit("30/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("60/minute", key_func=rate_limit_key_by_user)
async def list_feature_flag_audit_logs(
    request: Request,
    tenant_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    feature_name: str | None = Query(default=None, min_length=1, max_length=128),
    order: str = Query(default="desc", pattern="^(desc|asc)$"),
    current_user=Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if since is not None and until is not None and since > until:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid time range: since > until")
    if since is not None and until is None:
        max_since = datetime.now(since.tzinfo) - timedelta(days=settings.audit_max_lookback_days)
        if since < max_since:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lookback too large: max {settings.audit_max_lookback_days} days",
            )

    scoped_tenant_id: int | None
    if current_user.role.value == "super_admin":
        scoped_tenant_id = tenant_id
    else:
        scoped_tenant_id = int(current_user.tenant_id)

    items = AuditLogService().list_feature_flag_events(
        tenant_id=scoped_tenant_id,
        limit=limit + 1,
        offset=offset,
        since=since,
        until=until,
        feature_name=feature_name,
        order=order,
    )
    has_more = len(items) > limit
    page_items = items[:limit]
    next_offset = offset + limit if has_more else None
    payload = AuditLogEventsResponse(
        items=page_items,
        meta=AuditLogMeta(
            limit=limit,
            offset=offset,
            returned=len(page_items),
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


@router.get("/feature-flags/export", response_class=Response)
@limiter.limit("10/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("20/minute", key_func=rate_limit_key_by_user)
async def export_feature_flag_audit_logs(
    request: Request,
    tenant_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=1000, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    feature_name: str | None = Query(default=None, min_length=1, max_length=128),
    order: str = Query(default="desc", pattern="^(desc|asc)$"),
    current_user=Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if since is not None and until is not None and since > until:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid time range: since > until")
    if since is not None and until is None:
        max_since = datetime.now(since.tzinfo) - timedelta(days=settings.audit_max_lookback_days)
        if since < max_since:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lookback too large: max {settings.audit_max_lookback_days} days",
            )

    scoped_tenant_id: int | None
    if current_user.role.value == "super_admin":
        scoped_tenant_id = tenant_id
    else:
        scoped_tenant_id = int(current_user.tenant_id)

    csv_text, has_more = AuditLogService().export_feature_flag_events_csv(
        tenant_id=scoped_tenant_id,
        limit=limit,
        offset=offset,
        since=since,
        until=until,
        feature_name=feature_name,
        order=order,
    )
    lines = [line for line in csv_text.splitlines() if line.strip()]
    row_count = max(0, len(lines) - 1)  # exclude header
    checksum = hashlib.sha256(csv_text.encode("utf-8")).hexdigest()
    etag = f'W/"{checksum}"'
    next_offset = offset + limit if has_more else None
    if request.headers.get("if-none-match") == etag:
        return Response(
            status_code=304,
            headers={
                "ETag": etag,
                "Cache-Control": "private, max-age=30",
                "Vary": "Authorization, If-None-Match",
            },
        )
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="feature_flag_audit.csv"',
            "X-Export-Row-Count": str(row_count),
            "X-Export-SHA256": checksum,
            "X-Export-Has-More": "true" if has_more else "false",
            "X-Export-Next-Offset": str(next_offset) if next_offset is not None else "",
            "ETag": etag,
            "Cache-Control": "private, max-age=30",
            "Vary": "Authorization, If-None-Match",
        },
    )


@router.get("/feature-flags/names", response_model=AuditFeatureNamesResponse)
@limiter.limit("30/minute", key_func=rate_limit_key_by_ip)
@limiter.limit("60/minute", key_func=rate_limit_key_by_user)
async def list_feature_flag_audit_names(
    request: Request,
    tenant_id: int | None = Query(default=None, ge=1),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    current_user=Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if since is not None and until is not None and since > until:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid time range: since > until")
    if since is not None and until is None:
        max_since = datetime.now(since.tzinfo) - timedelta(days=settings.audit_max_lookback_days)
        if since < max_since:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lookback too large: max {settings.audit_max_lookback_days} days",
            )

    scoped_tenant_id: int | None
    if current_user.role.value == "super_admin":
        scoped_tenant_id = tenant_id
    else:
        scoped_tenant_id = int(current_user.tenant_id)

    items = AuditLogService().list_feature_names(
        tenant_id=scoped_tenant_id,
        since=since,
        until=until,
    )
    payload = AuditFeatureNamesResponse(items=items)
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
