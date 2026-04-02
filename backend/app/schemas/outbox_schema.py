from datetime import datetime
from pydantic import BaseModel, ConfigDict


class OutboxEventResponse(BaseModel):
    id: int
    tenant_id: int | None
    event_type: str
    status: str
    attempts: int
    error_message: str | None
    created_at: datetime
    available_at: datetime
    dispatched_at: datetime | None
    processed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class OutboxEventPageResponse(BaseModel):
    items: list[OutboxEventResponse]


class OutboxFlushResponse(BaseModel):
    dispatched: int


class OutboxRequeueResponse(BaseModel):
    requeued: int


class OutboxStatsResponse(BaseModel):
    queued: int
    processed: int
    failed: int
    dead: int
    dispatched: int
    pending: int | None = None
    processing: int | None = None


class OutboxRequeueOneResponse(BaseModel):
    requeued: bool


class OutboxRecoverResponse(BaseModel):
    recovered: int
