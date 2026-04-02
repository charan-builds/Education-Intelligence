from pydantic import BaseModel, Field


class SmartTestGenerateRequest(BaseModel):
    goal_id: int | None = Field(default=None, gt=0)
    question_count: int = Field(default=10, ge=3, le=30)


class SmartTestQuestionResponse(BaseModel):
    id: int
    topic_id: int
    topic_name: str
    difficulty: int
    difficulty_label: str
    question_type: str
    question_text: str
    answer_options: list[str] = []


class SmartTestTopicPlanResponse(BaseModel):
    topic_id: int
    topic_name: str
    mastery_score: float
    confidence: float
    target_difficulty: int
    selected_question_count: int


class SmartTestGenerateResponse(BaseModel):
    tenant_id: int
    user_id: int
    goal_id: int | None = None
    test_id: int
    started_at: str
    next_question_id: int | None = None
    persisted_session: bool = True
    question_count: int
    generated_from_weak_topics: list[SmartTestTopicPlanResponse] = []
    difficulty_mix: dict[str, int]
    repeated_question_count: int
    questions: list[SmartTestQuestionResponse] = []
