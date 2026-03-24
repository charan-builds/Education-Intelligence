from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class MentorChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    user_id: int
    tenant_id: int
    chat_history: list[dict[str, str]] = Field(default_factory=list)
    request_id: str | None = None


class MentorChatResponse(BaseModel):
    reply: str
    advisor_type: str
    used_ai: bool = False
    suggested_focus_topics: list[int] = Field(default_factory=list)
    why_recommended: list[str] = Field(default_factory=list)
    provider: str | None = None
    next_checkin_date: date | None = None
    session_summary: str = ""
    memory_summary: dict[str, Any] = Field(default_factory=dict)


class MentorSuggestionsResponse(BaseModel):
    suggestions: list[str]
    reasons: list[str] = Field(default_factory=list)


class MentorProgressAnalysisResponse(BaseModel):
    topic_improvements: dict[int, float]
    weekly_progress: list[dict[str, float | int | str]]
    recommended_focus: list[str]


class MentorNotificationItem(BaseModel):
    trigger: str
    severity: str
    title: str
    message: str


class MentorNotificationsResponse(BaseModel):
    notifications: list[MentorNotificationItem]


class AgentObservedStateResponse(BaseModel):
    roadmap_id: int | None = None
    completion_percent: float
    focus_score: float
    streak_days: int
    xp: int
    risk_level: str
    weak_topics: list[dict[str, Any]] = Field(default_factory=list)
    due_reviews: list[dict[str, Any]] = Field(default_factory=list)
    next_pending_topic: dict[str, Any] | None = None
    active_topic_count: int = 0
    completed_topic_count: int = 0
    last_activity: dict[str, Any] | None = None
    memory_summary: dict[str, Any] = Field(default_factory=dict)
    notification_candidates: list[dict[str, Any]] = Field(default_factory=list)


class AgentDecisionResponse(BaseModel):
    decision_type: str
    priority: str
    confidence: float
    topic_id: int | None = None
    title: str
    why: str


class AgentActionResponse(BaseModel):
    action_type: str
    status: str
    title: str
    details: dict[str, Any] = Field(default_factory=dict)
    why: str


class AutonomousAgentResponse(BaseModel):
    agent_mode: str
    observed_state: AgentObservedStateResponse
    decisions: list[AgentDecisionResponse] = Field(default_factory=list)
    actions: list[AgentActionResponse] = Field(default_factory=list)
    notifications: list[MentorNotificationItem] = Field(default_factory=list)
    memory_summary: dict[str, Any] = Field(default_factory=dict)
    next_best_topic_id: int | None = None
    cycle_summary: str
