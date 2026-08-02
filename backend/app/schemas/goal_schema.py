from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common_schema import PageMeta


class GoalResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: str
    skills_covered: list[str] | None = None
    estimated_duration_weeks: int | None = None
    difficulty_tag: str | None = None
    roadmap_preview: str | None = None
    is_recommended: bool = False

    model_config = ConfigDict(from_attributes=True)


class GoalPageResponse(BaseModel):
    items: list[GoalResponse]
    meta: PageMeta


class GoalCreateRequest(BaseModel):
    name: str
    description: str
    skills_covered: list[str] | None = None
    estimated_duration_weeks: int | None = None
    difficulty_tag: str | None = None
    roadmap_preview: str | None = None


class GoalUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    skills_covered: list[str] | None = None
    estimated_duration_weeks: int | None = None
    difficulty_tag: str | None = None
    roadmap_preview: str | None = None


class UserGoalSelectRequest(BaseModel):
    goal_id: int = Field(gt=0)


class UserGoalResponse(BaseModel):
    user_id: int
    goal_id: int
    is_active: bool
    goal: GoalResponse

    model_config = ConfigDict(from_attributes=True)


class GoalTopicCreateRequest(BaseModel):
    goal_id: int
    topic_id: int


class GoalTopicResponse(BaseModel):
    id: int
    goal_id: int
    topic_id: int

    model_config = ConfigDict(from_attributes=True)


class GoalTopicPageResponse(BaseModel):
    items: list[GoalTopicResponse]
    meta: PageMeta
