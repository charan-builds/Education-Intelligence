from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MarketplaceListingCreateRequest(BaseModel):
    topic_id: int | None = None
    resource_id: int | None = None
    listing_type: str = Field(min_length=2, max_length=32)
    title: str = Field(min_length=3, max_length=255)
    summary: str = Field(min_length=10, max_length=4000)
    price_cents: int = Field(ge=0, default=0)
    currency: str = Field(min_length=3, max_length=8, default="USD")


class MarketplaceReviewCreateRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    headline: str = Field(min_length=3, max_length=255)
    review_text: str = Field(min_length=10, max_length=2000)


class MarketplaceListingResponse(BaseModel):
    id: int
    tenant_id: int
    teacher_user_id: int
    topic_id: int | None = None
    resource_id: int | None = None
    listing_type: str
    title: str
    summary: str
    price_cents: int
    currency: str
    is_published: bool
    average_rating: float
    review_count: int
    created_at: datetime


class MarketplaceReviewResponse(BaseModel):
    id: int
    tenant_id: int
    listing_id: int
    reviewer_user_id: int
    rating: int
    headline: str
    review_text: str
    created_at: datetime


class PluginCreateRequest(BaseModel):
    key: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    plugin_type: str = Field(min_length=2, max_length=32)
    provider: str = Field(min_length=2, max_length=128)
    version: str = Field(min_length=1, max_length=32, default="1.0.0")
    config_json: str = Field(default="{}")


class PluginResponse(BaseModel):
    id: int
    tenant_id: int
    key: str
    name: str
    plugin_type: str
    provider: str
    version: str
    config_json: str
    is_enabled: bool
    created_at: datetime


class APIClientCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    scopes: list[str] = Field(default_factory=list)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=5000)


class APIClientResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    client_key: str
    scopes: list[str] = Field(default_factory=list)
    rate_limit_per_minute: int
    created_at: datetime


class SubscriptionPlanCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    monthly_price_cents: int = Field(ge=0)
    usage_price_cents: int = Field(ge=0, default=0)
    features: list[str] = Field(default_factory=list)


class SubscriptionPlanResponse(BaseModel):
    id: int
    tenant_id: int | None = None
    code: str
    name: str
    monthly_price_cents: int
    usage_price_cents: int
    features: list[str] = Field(default_factory=list)
    is_active: bool
    created_at: datetime


class TenantSubscriptionCreateRequest(BaseModel):
    plan_id: int
    seats: int = Field(default=25, ge=1)


class TenantSubscriptionResponse(BaseModel):
    id: int
    tenant_id: int
    plan_id: int
    status: str
    seats: int
    monthly_usage_units: int
    current_period_end: datetime
    created_at: datetime


class EcosystemOverviewResponse(BaseModel):
    marketplace_listing_count: int
    published_course_count: int
    plugin_count: int
    api_client_count: int
    active_subscription: TenantSubscriptionResponse | None = None
    monetization_snapshot: dict[str, int | str | None]
