from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LearnerFeatureSnapshotResponse(BaseModel):
    user_id: int
    tenant_id: int
    learning_speed: float
    retention_rate: float
    topic_difficulty_score: float
    user_engagement_score: float
    total_learning_events: int
    average_answer_accuracy: float
    average_time_spent_minutes: float


class MLModelRecordResponse(BaseModel):
    id: int
    tenant_id: int
    model_name: str
    version: str
    model_type: str
    metrics: dict[str, float | int | str]
    artifact_uri: str
    is_active: bool
    created_at: datetime


class MLTrainingRunResponse(BaseModel):
    id: int
    tenant_id: int
    model_name: str
    status: str
    trained_rows: int
    metrics: dict[str, float | int | str]
    created_at: datetime


class ModelTrainRequest(BaseModel):
    model_name: str = Field(min_length=2, max_length=64)


class RecommendationInferenceResponse(BaseModel):
    recommended_topic_ids: list[int] = Field(default_factory=list)
    engine: str
    model_version: str | None = None


class DifficultyInferenceResponse(BaseModel):
    topic_id: int
    predicted_difficulty_score: float
    predicted_label: str
    model_version: str | None = None


class DropoutInferenceResponse(BaseModel):
    user_id: int
    dropout_risk_score: float
    risk_level: str
    model_version: str | None = None
    recommended_interventions: list[str] = Field(default_factory=list)


class MLOutputOverviewResponse(BaseModel):
    latest_feature_snapshot: LearnerFeatureSnapshotResponse | None = None
    active_models: list[MLModelRecordResponse] = Field(default_factory=list)
    recent_training_runs: list[MLTrainingRunResponse] = Field(default_factory=list)
