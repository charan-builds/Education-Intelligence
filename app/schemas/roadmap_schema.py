from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.common_schema import PageMeta


class RoadmapGenerateRequest(BaseModel):
    goal_id: int
    test_id: int


class RoadmapStepUpdateRequest(BaseModel):
    progress_status: str


class RoadmapStepResponse(BaseModel):
    id: int
    topic_id: int
    phase: str | None = None
    estimated_time_hours: float
    difficulty: str
    priority: int
    deadline: datetime
    progress_status: str
    step_type: str = "core"
    rationale: str | None = None
    unlocks_topic_id: int | None = None
    is_revision: bool = False

    model_config = ConfigDict(from_attributes=True)


class RoadmapResponse(BaseModel):
    id: int
    user_id: int
    goal_id: int
    test_id: int
    status: str
    error_message: str | None = None
    generated_at: datetime
    steps: list[RoadmapStepResponse]

    model_config = ConfigDict(from_attributes=True)


class RoadmapPageResponse(BaseModel):
    items: list[RoadmapResponse]
    meta: PageMeta


class AdaptiveRoadmapResponse(BaseModel):
    roadmap_id: int
    reprioritized_steps: list[dict[str, Any]]
    inserted_revision: dict[str, Any] | None = None
    risk_prediction: dict[str, Any] | None = None
    weakness_clusters: list[dict[str, Any]] = []
    learning_profile: dict[str, Any] | None = None
