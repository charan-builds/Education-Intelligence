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
    fallback_used: bool = False
    fallback_reason: str | None = None
    suggested_focus_topics: list[int] = Field(default_factory=list)
    why_recommended: list[str] = Field(default_factory=list)
    provider: str | None = None
    latency_ms: float | None = None
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


class HybridMentorMatchResponse(BaseModel):
    mentor_id: int
    display_name: str
    email: str
    role: str
    match_score: int
    availability: str
    specialties: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    ai_handoff_summary: str


class HybridLearnerProfileResponse(BaseModel):
    user_id: int
    tenant_id: int
    completion_rate: float
    learning_style: str
    session_intensity: str
    weak_topics: list[str] = Field(default_factory=list)
    strong_topics: list[str] = Field(default_factory=list)
    human_support_needed: bool = True
    summary: str


class HybridCollaborationBriefResponse(BaseModel):
    session_goal: str
    ai_role: str
    human_role: str
    shared_context: list[str] = Field(default_factory=list)
    handoff_notes: list[str] = Field(default_factory=list)
    escalation_triggers: list[str] = Field(default_factory=list)


class HybridSupportChannelResponse(BaseModel):
    channel_type: str
    title: str
    description: str
    href: str
    realtime_enabled: bool = True
    why: str


class HybridMentorshipOverviewResponse(BaseModel):
    learner_profile: HybridLearnerProfileResponse
    mentor_matches: list[HybridMentorMatchResponse] = Field(default_factory=list)
    collaboration_brief: HybridCollaborationBriefResponse
    live_support_channels: list[HybridSupportChannelResponse] = Field(default_factory=list)


class HybridSessionPlanRequest(BaseModel):
    learner_id: int | None = None
    mentor_id: int | None = None
    topic_id: int | None = None


class HybridSessionPlanResponse(BaseModel):
    mentor_id: int | None = None
    mentor_name: str
    session_title: str
    agenda: list[str] = Field(default_factory=list)
    ai_prep_notes: list[str] = Field(default_factory=list)
    mentor_focus: list[str] = Field(default_factory=list)
    follow_up_actions: list[str] = Field(default_factory=list)
