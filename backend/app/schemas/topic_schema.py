from pydantic import BaseModel, ConfigDict

from app.schemas.common_schema import PageMeta


class TopicPracticeQuestion(BaseModel):
    id: int
    topic_id: int | None = None
    difficulty: int
    question_type: str = "short_text"
    question_text: str
    answer_options: list[str] = []


class TopicDetailResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: str
    examples: list[str]
    practice_questions: list[TopicPracticeQuestion]


class TopicSummaryResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: str


class TopicPageResponse(BaseModel):
    items: list[TopicSummaryResponse]
    meta: PageMeta


class KnowledgeGraphNodeResponse(BaseModel):
    id: int
    node_type: str
    name: str
    description: str
    mastery_score: float | None = None
    cluster: str
    status: str
    is_completed: bool = False
    is_weak: bool = False
    is_locked: bool = False
    skill_names: list[str] = []
    prerequisite_count: int = 0


class KnowledgeGraphEdgeResponse(BaseModel):
    source_id: int
    target_id: int
    edge_type: str
    strength: float = 1.0


class KnowledgeGraphClusterResponse(BaseModel):
    label: str
    topic_count: int


class KnowledgeGraphSummaryResponse(BaseModel):
    topic_count: int
    skill_count: int
    edge_count: int
    completed_topic_count: int = 0
    weak_topic_count: int
    locked_topic_count: int = 0


class KnowledgeGraphResponse(BaseModel):
    nodes: list[KnowledgeGraphNodeResponse]
    edges: list[KnowledgeGraphEdgeResponse]
    clusters: list[KnowledgeGraphClusterResponse]
    summary: KnowledgeGraphSummaryResponse


class TopicReasoningNodeResponse(BaseModel):
    topic_id: int
    topic_name: str
    mastery_score: float | None = None
    status: str


class SimilarTopicResponse(BaseModel):
    topic_id: int
    topic_name: str
    similarity_percent: float
    cluster: str
    mastery_score: float | None = None


class RecommendedTopicResponse(BaseModel):
    topic_id: int
    topic_name: str
    reason: str
    readiness_percent: float


class TopicReasoningResponse(BaseModel):
    target_topic_id: int
    target_topic_name: str
    dependency_resolution: list[TopicReasoningNodeResponse]
    shortest_learning_path: list[TopicReasoningNodeResponse]
    missing_foundations: list[TopicReasoningNodeResponse]
    inferred_missing_topics: list[TopicReasoningNodeResponse]
    similar_topics: list[SimilarTopicResponse]
    clusters: list[str]
    recommended_next_topics: list[RecommendedTopicResponse]
    readiness_percent: float


class TopicCreateRequest(BaseModel):
    name: str
    description: str


class TopicUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class TopicPrerequisiteCreateRequest(BaseModel):
    topic_id: int
    prerequisite_topic_id: int


class TopicPrerequisiteResponse(BaseModel):
    id: int
    topic_id: int
    prerequisite_topic_id: int

    model_config = ConfigDict(from_attributes=True)


class TopicPrerequisitePageResponse(BaseModel):
    items: list[TopicPrerequisiteResponse]
    meta: PageMeta


class QuestionCreateRequest(BaseModel):
    topic_id: int
    difficulty: int
    question_type: str
    question_text: str
    correct_answer: str
    accepted_answers: list[str] = []
    answer_options: list[str] = []


class QuestionUpdateRequest(BaseModel):
    difficulty: int | None = None
    question_type: str | None = None
    question_text: str | None = None
    correct_answer: str | None = None
    accepted_answers: list[str] | None = None
    answer_options: list[str] | None = None


class QuestionResponse(BaseModel):
    id: int
    topic_id: int
    difficulty: int
    question_type: str
    question_text: str
    correct_answer: str
    accepted_answers: list[str]
    answer_options: list[str]

    model_config = ConfigDict(from_attributes=True)


class QuestionPageResponse(BaseModel):
    items: list[QuestionResponse]
    meta: PageMeta


class QuestionImportItem(BaseModel):
    topic_id: int
    difficulty: int
    question_type: str
    question_text: str
    correct_answer: str
    accepted_answers: list[str] = []
    answer_options: list[str] = []


class QuestionImportRequest(BaseModel):
    items: list[QuestionImportItem]


class QuestionImportResponse(BaseModel):
    created: int


class TopicExplanationRequest(BaseModel):
    topic_name: str


class TopicExplanationResponse(BaseModel):
    topic_name: str
    explanation: str
    examples: list[str]
    use_cases: list[str]
    suggestions: list[str] = []
    next_steps: list[str] = []


class AIQuestionGenerationRequest(BaseModel):
    topic: str
    difficulty: str
    count: int = 3


class AIGeneratedQuestionResponse(BaseModel):
    question_type: str
    question_text: str
    answer_options: list[str]
    correct_answer: str
    explanation: str


class AIQuestionGenerationResponse(BaseModel):
    topic: str
    difficulty: str
    questions: list[AIGeneratedQuestionResponse]
    suggestions: list[str] = []
    next_steps: list[str] = []
