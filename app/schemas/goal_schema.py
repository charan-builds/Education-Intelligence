from pydantic import BaseModel, ConfigDict

from app.schemas.common_schema import PageMeta


class GoalResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class GoalPageResponse(BaseModel):
    items: list[GoalResponse]
    meta: PageMeta


class GoalCreateRequest(BaseModel):
    name: str
    description: str


class GoalUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None


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
