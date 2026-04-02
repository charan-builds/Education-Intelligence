from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FeatureFlagResponse(BaseModel):
    id: int
    tenant_id: int
    feature_name: str
    enabled: bool
    rollout_percentage: int = 100
    audience_filter_json: str = "{}"
    experiment_key: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeatureFlagPageMeta(BaseModel):
    limit: int
    offset: int
    returned: int
    total: int
    has_more: bool
    next_offset: int | None


class FeatureFlagPageResponse(BaseModel):
    items: list[FeatureFlagResponse]
    meta: FeatureFlagPageMeta


class FeatureFlagUpdateRequest(BaseModel):
    enabled: bool
    tenant_id: int | None = None
    rollout_percentage: int = Field(default=100, ge=0, le=100)
    audience_filter: dict[str, str | int | bool] = Field(default_factory=dict)
    experiment_key: str | None = None


class FeatureFlagCatalogResponse(BaseModel):
    items: list[str]
