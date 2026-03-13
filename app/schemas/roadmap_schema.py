from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common_schema import PageMeta


class RoadmapGenerateRequest(BaseModel):
    goal_id: int
    test_id: int


class RoadmapStepResponse(BaseModel):
    id: int
    topic_id: int
    estimated_time_hours: float
    difficulty: str
    priority: int
    deadline: datetime
    progress_status: str

    model_config = ConfigDict(from_attributes=True)


class RoadmapResponse(BaseModel):
    id: int
    user_id: int
    goal_id: int
    generated_at: datetime
    steps: list[RoadmapStepResponse]

    model_config = ConfigDict(from_attributes=True)


class RoadmapPageResponse(BaseModel):
    items: list[RoadmapResponse]
    meta: PageMeta
