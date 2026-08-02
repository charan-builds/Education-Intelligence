from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.roadmap_schema import RoadmapResponse


class DiagnosticQuestionOptionResponse(BaseModel):
    key: str
    text: str


class DiagnosticStartRequest(BaseModel):
    user_id: int | None = Field(default=None, gt=0)
    goal_id: int = Field(gt=0)
    question_count: int = Field(default=20, ge=1, le=30)


class DiagnosticDifficultyResponse(BaseModel):
    difficulty_level: int = Field(ge=1, le=3)
    difficulty_label: Literal["easy", "medium", "hard"]


class DiagnosticStartQuestionResponse(DiagnosticDifficultyResponse):
    id: int
    topic_id: int
    question_type: str
    question_text: str
    options: list[DiagnosticQuestionOptionResponse] = Field(default_factory=list)


class DiagnosticStartResponse(BaseModel):
    test_id: int | None = None
    id: int
    user_id: int
    goal_id: int
    started_at: datetime
    test_duration: int = Field(default=20, ge=1)
    status: str = "started"
    completed_at: datetime | None
    expired_at: datetime | None = None
    questions: list[DiagnosticStartQuestionResponse] = Field(default_factory=list)

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
    answers: list["DiagnosticSubmitAnswerRequest"] = Field(default_factory=list)


class DiagnosticSubmitAnswerRequest(BaseModel):
    question_id: int = Field(gt=0)
    selected_answer: str = Field(min_length=1, max_length=5000)
    time_taken: float = Field(ge=0, le=7200)

    @field_validator("selected_answer")
    @classmethod
    def _validate_selected_answer(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("selected_answer must not be blank")
        return normalized


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
    answered_count: int = 0
    total_score: float = 0.0
    percentage_score: float = 0.0
    answers: list["DiagnosticSubmittedAnswerResponse"] = Field(default_factory=list)


class DiagnosticSubmittedAnswerResponse(DiagnosticDifficultyResponse):
    question_id: int
    selected_answer: str
    score: float
    time_taken: float


class DiagnosticResultResponse(BaseModel):
    test_id: int
    topic_scores: dict[int, float]
    weak_topic_ids: list[int] = []
    foundation_gap_topic_ids: list[int] = []
    recommendation_levels: dict[int, str] = {}
    roadmap: RoadmapResponse | None = None


class DiagnosticResumeResponse(DiagnosticStartResponse):
    answered_count: int = 0


class DiagnosticNextQuestionRequest(BaseModel):
    test_id: int = Field(gt=0)


class DiagnosticQuestionResponse(DiagnosticDifficultyResponse):
    test_id: int
    id: int
    topic_id: int
    adaptive_strategy: str = "adaptive_targeted"
    target_topic_id: int | None = None
    target_difficulty: int | None = None
    weakness_topic_ids: list[int] = []
    question_type: str = "short_text"
    question_text: str
    answer_options: list[str] = []
