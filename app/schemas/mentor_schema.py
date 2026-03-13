from pydantic import BaseModel, Field


class MentorChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    user_id: int
    tenant_id: int


class MentorChatResponse(BaseModel):
    reply: str
    advisor_type: str


class MentorSuggestionsResponse(BaseModel):
    suggestions: list[str]


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
