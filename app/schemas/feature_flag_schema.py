from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FeatureFlagResponse(BaseModel):
    id: int
    tenant_id: int
    feature_name: str
    enabled: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeatureFlagPageResponse(BaseModel):
    items: list[FeatureFlagResponse]


class FeatureFlagUpdateRequest(BaseModel):
    enabled: bool
    tenant_id: int | None = None


class FeatureFlagCatalogResponse(BaseModel):
    items: list[str]
