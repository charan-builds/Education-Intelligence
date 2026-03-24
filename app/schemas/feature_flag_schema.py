from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FeatureFlagResponse(BaseModel):
    id: int
    tenant_id: int
    feature_name: str
    enabled: bool
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


class FeatureFlagCatalogResponse(BaseModel):
    items: list[str]
