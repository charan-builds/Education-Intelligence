from pydantic import BaseModel, ConfigDict

from app.schemas.common_schema import PageMeta


class GoalResponse(BaseModel):
    id: int
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class GoalPageResponse(BaseModel):
    items: list[GoalResponse]
    meta: PageMeta
