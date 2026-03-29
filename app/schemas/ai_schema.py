from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AIChatHistoryItemResponse(BaseModel):
    request_id: str
    role: str
    message: str
    response: str | None = None
    status: str
    created_at: datetime


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    chat_history: list[dict[str, str]] = Field(default_factory=list)


class AIChatResponse(BaseModel):
    request_id: str
    reply: str
    advisor_type: str
    used_ai: bool = False
    suggested_focus_topics: list[int] = Field(default_factory=list)
    why_recommended: list[str] = Field(default_factory=list)
    provider: str | None = None
    next_checkin_date: str | None = None
    session_summary: str = ""
    memory_summary: dict[str, Any] = Field(default_factory=dict)
    prompt_context: dict[str, Any] = Field(default_factory=dict)
    history: list[AIChatHistoryItemResponse] = Field(default_factory=list)
