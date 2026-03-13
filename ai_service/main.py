from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Learning Platform AI Service", version="0.1.0")


class TopicScore(BaseModel):
    topic_id: int
    score: float = Field(ge=0, le=100)


class LearningPathRequest(BaseModel):
    user_id: int
    tenant_id: int
    goal: str
    topic_scores: list[TopicScore] = Field(default_factory=list)
    learning_profile: dict[str, Any] = Field(default_factory=dict)


class LearningPathStep(BaseModel):
    topic_id: int
    priority: int
    reason: str
    estimated_time_hours: float


class LearningPathResponse(BaseModel):
    user_id: int
    tenant_id: int
    goal: str
    strategy: Literal["placeholder_rule_v1"]
    recommended_steps: list[LearningPathStep]


class MentorResponseRequest(BaseModel):
    user_id: int
    tenant_id: int
    message: str
    roadmap: list[dict[str, Any]] = Field(default_factory=list)
    weak_topics: list[int] = Field(default_factory=list)
    learning_profile: dict[str, Any] = Field(default_factory=dict)


class MentorResponse(BaseModel):
    user_id: int
    tenant_id: int
    response: str
    suggested_focus_topics: list[int]
    next_checkin_date: date


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict-learning-path", response_model=LearningPathResponse)
async def predict_learning_path(payload: LearningPathRequest) -> LearningPathResponse:
    # Deterministic placeholder strategy until ML model integration is added.
    weak_first = sorted(payload.topic_scores, key=lambda item: (item.score, item.topic_id))
    selected = weak_first[:10]

    steps: list[LearningPathStep] = []
    for index, topic in enumerate(selected, start=1):
        deficit = max(0.0, 100.0 - float(topic.score))
        estimated = round(1.5 + (deficit / 20.0), 2)
        reason = "weak_foundation" if topic.score < 70 else "goal_alignment"
        steps.append(
            LearningPathStep(
                topic_id=topic.topic_id,
                priority=index,
                reason=reason,
                estimated_time_hours=estimated,
            )
        )

    return LearningPathResponse(
        user_id=payload.user_id,
        tenant_id=payload.tenant_id,
        goal=payload.goal,
        strategy="placeholder_rule_v1",
        recommended_steps=steps,
    )


@app.post("/mentor-response", response_model=MentorResponse)
async def mentor_response(payload: MentorResponseRequest) -> MentorResponse:
    weak = sorted(set(payload.weak_topics))[:5]
    profile = str(payload.learning_profile.get("profile_type", "balanced"))
    advice = (
        f"Profile: {profile}. Focus first on weak topics {weak if weak else 'none identified'}. "
        "Use 45-minute sessions with one short recap after each session."
    )

    return MentorResponse(
        user_id=payload.user_id,
        tenant_id=payload.tenant_id,
        response=advice,
        suggested_focus_topics=weak,
        next_checkin_date=date.today() + timedelta(days=7),
    )
