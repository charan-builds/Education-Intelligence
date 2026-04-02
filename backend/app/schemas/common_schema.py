from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    cursor: str | None = None


class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int
    next_offset: int | None
    next_cursor: str | None = None
