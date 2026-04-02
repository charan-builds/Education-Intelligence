from typing import Any

from pydantic import BaseModel


class AuditLogMeta(BaseModel):
    limit: int
    offset: int
    returned: int
    has_more: bool
    next_offset: int | None


class AuditLogEventsResponse(BaseModel):
    items: list[dict[str, Any]]
    meta: AuditLogMeta


class AuditFeatureNamesResponse(BaseModel):
    items: list[str]
