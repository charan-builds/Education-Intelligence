from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DiagnosticStartRequest(BaseModel):
    goal_id: int


class DiagnosticStartResponse(BaseModel):
    id: int
    user_id: int
    goal_id: int
    started_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AnswerPayload(BaseModel):
    question_id: int
    user_answer: str
    score: float | None = None
    time_taken: float


class DiagnosticSubmitRequest(BaseModel):
    test_id: int
    answers: list[AnswerPayload]


class DiagnosticResultResponse(BaseModel):
    test_id: int
    topic_scores: dict[int, float]


class DiagnosticNextQuestionRequest(BaseModel):
    goal_id: int
    previous_answers: list[AnswerPayload] = []


class DiagnosticQuestionResponse(BaseModel):
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
