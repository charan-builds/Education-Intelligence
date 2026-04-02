from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.ecosystem_service import EcosystemService
from app.core.dependencies import get_current_user, require_roles
from app.infrastructure.database import get_db_session
from app.schemas.ecosystem_schema import (
    APIClientCreateRequest,
    APIClientResponse,
    EcosystemOverviewResponse,
    MarketplaceListingCreateRequest,
    MarketplaceListingResponse,
    MarketplaceReviewCreateRequest,
    MarketplaceReviewResponse,
    PluginCreateRequest,
    PluginResponse,
    SubscriptionPlanCreateRequest,
    SubscriptionPlanResponse,
    TenantSubscriptionCreateRequest,
    TenantSubscriptionResponse,
)

router = APIRouter(prefix="/ecosystem", tags=["ecosystem"])


def _api_client_response(row) -> APIClientResponse:
    return APIClientResponse(
        id=row.id,
        tenant_id=row.tenant_id,
        name=row.name,
        client_key=row.client_key,
        scopes=json.loads(row.scopes_json or "[]"),
        rate_limit_per_minute=row.rate_limit_per_minute,
        created_at=row.created_at,
    )


def _plan_response(row) -> SubscriptionPlanResponse:
    return SubscriptionPlanResponse(
        id=row.id,
        tenant_id=row.tenant_id,
        code=row.code,
        name=row.name,
        monthly_price_cents=row.monthly_price_cents,
        usage_price_cents=row.usage_price_cents,
        features=json.loads(row.features_json or "[]"),
        is_active=row.is_active,
        created_at=row.created_at,
    )


@router.get("/overview", response_model=EcosystemOverviewResponse)
async def ecosystem_overview(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    payload = await EcosystemService(db).get_overview(tenant_id=current_user.tenant_id)
    subscription = payload["active_subscription"]
    return EcosystemOverviewResponse(
        marketplace_listing_count=payload["marketplace_listing_count"],
        published_course_count=payload["published_course_count"],
        plugin_count=payload["plugin_count"],
        api_client_count=payload["api_client_count"],
        active_subscription=(
            TenantSubscriptionResponse(
                id=subscription.id,
                tenant_id=subscription.tenant_id,
                plan_id=subscription.plan_id,
                status=subscription.status,
                seats=subscription.seats,
                monthly_usage_units=subscription.monthly_usage_units,
                current_period_end=subscription.current_period_end,
                created_at=subscription.created_at,
            )
            if subscription is not None
            else None
        ),
        monetization_snapshot=payload["monetization_snapshot"],
    )


@router.get("/marketplace", response_model=list[MarketplaceListingResponse])
async def list_marketplace(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    rows = await EcosystemService(db).list_marketplace(tenant_id=current_user.tenant_id)
    return [MarketplaceListingResponse.model_validate(row, from_attributes=True) for row in rows]


@router.post("/marketplace", response_model=MarketplaceListingResponse)
async def create_marketplace_listing(
    payload: MarketplaceListingCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("teacher", "admin", "super_admin")),
):
    row = await EcosystemService(db).create_listing(
        tenant_id=current_user.tenant_id,
        teacher_user_id=current_user.id,
        topic_id=payload.topic_id,
        resource_id=payload.resource_id,
        listing_type=payload.listing_type,
        title=payload.title,
        summary=payload.summary,
        price_cents=payload.price_cents,
        currency=payload.currency,
    )
    return MarketplaceListingResponse.model_validate(row, from_attributes=True)


@router.post("/marketplace/{listing_id}/reviews", response_model=MarketplaceReviewResponse)
async def create_marketplace_review(
    listing_id: int,
    payload: MarketplaceReviewCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    row = await EcosystemService(db).create_review(
        tenant_id=current_user.tenant_id,
        listing_id=listing_id,
        reviewer_user_id=current_user.id,
        rating=payload.rating,
        headline=payload.headline,
        review_text=payload.review_text,
    )
    return MarketplaceReviewResponse.model_validate(row, from_attributes=True)


@router.get("/plugins", response_model=list[PluginResponse])
async def list_plugins(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    rows = await EcosystemService(db).list_plugins(tenant_id=current_user.tenant_id)
    return [PluginResponse.model_validate(row, from_attributes=True) for row in rows]


@router.post("/plugins", response_model=PluginResponse)
async def create_plugin(
    payload: PluginCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    row = await EcosystemService(db).create_plugin(
        tenant_id=current_user.tenant_id,
        key=payload.key,
        name=payload.name,
        plugin_type=payload.plugin_type,
        provider=payload.provider,
        version=payload.version,
        config_json=payload.config_json,
    )
    return PluginResponse.model_validate(row, from_attributes=True)


@router.get("/api-clients", response_model=list[APIClientResponse])
async def list_api_clients(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    rows = await EcosystemService(db).list_api_clients(tenant_id=current_user.tenant_id)
    return [_api_client_response(row) for row in rows]


@router.post("/api-clients", response_model=APIClientResponse)
async def create_api_client(
    payload: APIClientCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    row = await EcosystemService(db).create_api_client(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        scopes=payload.scopes,
        rate_limit_per_minute=payload.rate_limit_per_minute,
    )
    return _api_client_response(row)


@router.get("/subscription-plans", response_model=list[SubscriptionPlanResponse])
async def list_subscription_plans(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    rows = await EcosystemService(db).list_subscription_plans()
    return [_plan_response(row) for row in rows]


@router.post("/subscription-plans", response_model=SubscriptionPlanResponse)
async def create_subscription_plan(
    payload: SubscriptionPlanCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("super_admin", "admin")),
):
    row = await EcosystemService(db).create_subscription_plan(
        tenant_id=current_user.tenant_id if current_user.role.value == "admin" else None,
        code=payload.code,
        name=payload.name,
        monthly_price_cents=payload.monthly_price_cents,
        usage_price_cents=payload.usage_price_cents,
        features=payload.features,
    )
    return _plan_response(row)


@router.post("/subscription", response_model=TenantSubscriptionResponse)
async def assign_subscription(
    payload: TenantSubscriptionCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles("admin", "super_admin")),
):
    row = await EcosystemService(db).assign_subscription(
        tenant_id=current_user.tenant_id,
        plan_id=payload.plan_id,
        seats=payload.seats,
    )
    return TenantSubscriptionResponse.model_validate(row, from_attributes=True)
