from __future__ import annotations

from pydantic import BaseModel, Field


class CareerRoleMatchResponse(BaseModel):
    role_id: int
    role_name: str
    category: str
    readiness_percent: float
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)


class JobReadinessResponse(BaseModel):
    user_id: int
    tenant_id: int
    readiness_percent: float
    confidence_label: str
    breakdown: dict[str, float]
    top_role_matches: list[CareerRoleMatchResponse] = Field(default_factory=list)
    alternative_paths: list[CareerRoleMatchResponse] = Field(default_factory=list)


class ResumePreviewResponse(BaseModel):
    headline: str
    summary: str
    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class InterviewPrepRequest(BaseModel):
    role_name: str = Field(min_length=2, max_length=255)
    difficulty: str = Field(default="intermediate", min_length=2, max_length=32)
    count: int = Field(default=5, ge=1, le=5)


class InterviewQuestionResponse(BaseModel):
    question_type: str
    question_text: str
    answer_options: list[str] = Field(default_factory=list)
    correct_answer: str
    explanation: str


class InterviewPrepResponse(BaseModel):
    role_name: str
    mock_interview_prompt: str
    questions: list[InterviewQuestionResponse] = Field(default_factory=list)


class CareerOverviewResponse(BaseModel):
    readiness: JobReadinessResponse
    resume_preview: ResumePreviewResponse
    career_path: dict
