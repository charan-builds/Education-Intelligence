from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.roadmap_schema import RoadmapResponse


class DiagnosticStartRequest(BaseModel):
    goal_id: int = Field(gt=0)


class DiagnosticStartResponse(BaseModel):
    id: int
    user_id: int
    goal_id: int
    started_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AnswerPayload(BaseModel):
    question_id: int = Field(gt=0)
    user_answer: str = Field(min_length=1, max_length=5000)
    score: float | None = None
    time_taken: float = Field(ge=0, le=7200)

    @field_validator("user_answer")
    @classmethod
    def _validate_user_answer(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("user_answer must not be blank")
        return normalized


class DiagnosticAnswerRequest(BaseModel):
    test_id: int = Field(gt=0)
    question_id: int = Field(gt=0)
    user_answer: str = Field(min_length=1, max_length=5000)
    time_taken: float = Field(ge=0, le=7200)

    @field_validator("user_answer")
    @classmethod
    def _validate_answer_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("user_answer must not be blank")
        return normalized


class DiagnosticAnswerResponse(BaseModel):
    test_id: int
    question_id: int
    answered_count: int
    completed_at: datetime | None
    adaptive_decision: dict | None = None


class DiagnosticSubmitRequest(BaseModel):
    test_id: int = Field(gt=0)


class DiagnosticAdaptiveTopicLevelResponse(BaseModel):
    topic_id: int
    level: str
    average_accuracy: float
    average_time_taken: float
    average_attempts: float
    recommended_difficulty: int


class DiagnosticAdaptiveSummaryResponse(BaseModel):
    topic_levels: list[DiagnosticAdaptiveTopicLevelResponse] = []


class DiagnosticSubmitResponse(DiagnosticStartResponse):
    adaptive_summary: DiagnosticAdaptiveSummaryResponse


class DiagnosticResultResponse(BaseModel):
    test_id: int
    topic_scores: dict[int, float]
    roadmap: RoadmapResponse | None = None


class DiagnosticResumeResponse(DiagnosticStartResponse):
    answered_count: int = 0


class DiagnosticNextQuestionRequest(BaseModel):
    test_id: int = Field(gt=0)


class DiagnosticQuestionResponse(BaseModel):
    test_id: int
    id: int
    topic_id: int
    difficulty: int
    difficulty_label: str
    adaptive_strategy: str = "adaptive_targeted"
    target_topic_id: int | None = None
    target_difficulty: int | None = None
    weakness_topic_ids: list[int] = []
    question_type: str = "short_text"
    question_text: str
    answer_options: list[str] = []
