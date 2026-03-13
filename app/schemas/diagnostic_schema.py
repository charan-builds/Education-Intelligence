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
    score: float
    time_taken: float


class DiagnosticSubmitRequest(BaseModel):
    test_id: int
    answers: list[AnswerPayload]


class DiagnosticResultResponse(BaseModel):
    test_id: int
    topic_scores: dict[int, float]
