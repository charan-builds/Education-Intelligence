from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.models.tenant import TenantType
from app.schemas.common_schema import PageMeta


class TenantCreateRequest(BaseModel):
    name: str
    type: TenantType


class TenantResponse(BaseModel):
    id: int
    name: str
    type: TenantType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantPageResponse(BaseModel):
    items: list[TenantResponse]
    meta: PageMeta
