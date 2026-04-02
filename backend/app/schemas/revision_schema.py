from pydantic import BaseModel, Field


class RevisionTopicItemResponse(BaseModel):
    topic_id: int
    topic_name: str
    score: float
    retention_score: float
    revision_interval_days: int
    review_due_at: str | None = None
    last_seen: str | None = None
    is_due: bool


class RevisionTodayResponse(BaseModel):
    tenant_id: int
    user_id: int
    generated_at: str
    due_count: int
    revisions: list[RevisionTopicItemResponse] = Field(default_factory=list)
