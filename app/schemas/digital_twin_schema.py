from typing import Any

from pydantic import BaseModel


class TwinTopicSignalResponse(BaseModel):
    topic_id: int
    topic_name: str
    score: float
    retention_score: float | None = None


class TwinBehaviorPatternsResponse(BaseModel):
    average_session_minutes: float
    study_event_count: int
    cadence_pattern: str
    engagement_pattern: str
    profile_type: str
    confidence: float
    consistency: float
    stamina: float


class TwinRoadmapStateResponse(BaseModel):
    total_steps: int
    completed_steps: int
    completion_percent: float


class DigitalTwinCurrentModelResponse(BaseModel):
    learner_summary: str
    strengths: list[TwinTopicSignalResponse]
    weaknesses: list[TwinTopicSignalResponse]
    learning_speed: float
    memory_retention: float
    behavior_patterns: TwinBehaviorPatternsResponse
    roadmap_state: TwinRoadmapStateResponse
    retention_summary: dict[str, Any]
    twin_confidence: float


class DigitalTwinSimulationResponse(BaseModel):
    strategy: str
    daily_study_hours: float
    estimated_completion_date: str
    progress_curve: list[dict[str, Any]]


class DigitalTwinStrategyResponse(BaseModel):
    strategy: str
    summary: str
    predicted_completion_date: str
    predicted_readiness_percent: float
    predicted_retention_percent: float
    tradeoff: str


class DigitalTwinDecisionSupportResponse(BaseModel):
    recommended_strategy: DigitalTwinStrategyResponse
    strategy_comparison: list[DigitalTwinStrategyResponse]
    recommended_learning_path: list[str]
    why: list[str]


class DigitalTwinPredictionsResponse(BaseModel):
    risk_prediction: dict[str, Any]
    baseline: DigitalTwinSimulationResponse
    accelerated_focus: DigitalTwinSimulationResponse
    retention_first: DigitalTwinSimulationResponse


class DigitalTwinResponse(BaseModel):
    user_id: int
    tenant_id: int
    current_model: DigitalTwinCurrentModelResponse
    predictions: DigitalTwinPredictionsResponse
    decision_support: DigitalTwinDecisionSupportResponse
