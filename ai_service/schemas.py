from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class TopicScore(BaseModel):
    topic_id: int
    score: float = Field(ge=0, le=100)


class PromptSection(BaseModel):
    explanation: str
    suggestions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class LearningPathRequest(BaseModel):
    user_id: int
    tenant_id: int
    goal: str
    topic_scores: list[TopicScore] = Field(default_factory=list)
    prerequisites: list[tuple[int, int]] = Field(default_factory=list)
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
    strategy: str
    recommended_steps: list[LearningPathStep]
    reasoning: PromptSection


class MentorResponseRequest(BaseModel):
    user_id: int
    tenant_id: int
    goal: str | None = None
    message: str
    weak_topics: list[int] = Field(default_factory=list)
    roadmap: list[dict[str, Any]] = Field(default_factory=list)
    learning_profile: dict[str, Any] = Field(default_factory=dict)
    chat_history: list[dict[str, str]] = Field(default_factory=list)
    mentor_context: dict[str, Any] = Field(default_factory=dict)


class MentorResponse(BaseModel):
    user_id: int
    tenant_id: int
    response: str
    suggested_focus_topics: list[int] = Field(default_factory=list)
    provider: str | None = None
    next_checkin_date: date | None = None
    guidance: PromptSection
    session_summary: str = ""
    memory_update: dict[str, Any] = Field(default_factory=dict)


class ProgressAnalysisRequest(BaseModel):
    user_id: int
    tenant_id: int
    completion_percent: float = Field(ge=0, le=100)
    weak_topics: list[int] = Field(default_factory=list)


class ProgressAnalysisResponse(BaseModel):
    user_id: int
    tenant_id: int
    summary: str
    recommended_focus_topics: list[int] = Field(default_factory=list)
    guidance: PromptSection


class TopicExplainRequest(BaseModel):
    topic_name: str = Field(min_length=1, max_length=200)


class TopicExplainResponse(BaseModel):
    topic_name: str
    explanation: str
    examples: list[str] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list)
    guidance: PromptSection


class GeneratedQuestion(BaseModel):
    question_type: str
    question_text: str
    answer_options: list[str] = Field(default_factory=list)
    correct_answer: str
    explanation: str


class QuestionGenerationRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=200)
    difficulty: str = Field(min_length=1, max_length=32)
    count: int = Field(default=3, ge=1, le=5)


class QuestionGenerationResponse(BaseModel):
    topic: str
    difficulty: str
    questions: list[GeneratedQuestion] = Field(default_factory=list)
    guidance: PromptSection
