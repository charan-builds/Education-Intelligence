from pydantic import BaseModel

from app.schemas.analytics_schema import LearnerRoadmapProgressResponse


class DashboardVelocityPointResponse(BaseModel):
    label: str
    minutes: float
    completed_steps: int


class WeakTopicHeatmapItemResponse(BaseModel):
    topic_id: int
    topic_name: str
    score: float
    mastery_delta: float
    confidence: float


class MentorSuggestionCardResponse(BaseModel):
    id: int
    title: str
    message: str
    why: str
    topic_id: int | None
    is_ai_generated: bool


class SkillGraphNodeResponse(BaseModel):
    topic_id: int
    topic_name: str
    status: str
    dependencies: list[int]


class BadgeCardResponse(BaseModel):
    name: str
    description: str
    awarded_at: str


class LeaderboardEntryResponse(BaseModel):
    rank: int
    user_id: int
    name: str
    xp: int
    is_current_user: bool


class GamificationSummaryResponse(BaseModel):
    badges: list[BadgeCardResponse]
    leaderboard: list[LeaderboardEntryResponse]


class ActivityItemResponse(BaseModel):
    event_type: str
    created_at: str
    topic_id: int | None


class RetentionReviewItemResponse(BaseModel):
    topic_id: int
    topic_name: str
    score: float
    retention_score: float
    review_interval_days: int
    review_due_at: str | None
    is_due: bool


class ResourceRecommendationResponse(BaseModel):
    id: int
    topic_id: int
    topic_name: str
    title: str
    resource_type: str
    difficulty: str
    rating: float
    url: str


class StudentRetentionSummaryResponse(BaseModel):
    tenant_id: int
    user_id: int
    average_retention_score: float
    due_reviews: list[RetentionReviewItemResponse]
    upcoming_reviews: list[RetentionReviewItemResponse]
    recommended_resources: list[ResourceRecommendationResponse]


class StudentDashboardResponse(BaseModel):
    tenant_id: int
    user_id: int
    completion_percent: float
    streak_days: int
    focus_score: float
    xp: int
    roadmap_progress: dict[str, int | float]
    learning_velocity: list[DashboardVelocityPointResponse]
    weak_topic_heatmap: list[WeakTopicHeatmapItemResponse]
    weak_topics: list[WeakTopicHeatmapItemResponse]
    weakness_clusters: list[dict] = []
    learning_profile: dict = {}
    mentor_suggestions: list[MentorSuggestionCardResponse]
    retention: StudentRetentionSummaryResponse
    skill_graph: list[SkillGraphNodeResponse]
    gamification: GamificationSummaryResponse
    recent_activity: list[ActivityItemResponse]


class TeacherTopicClusterResponse(BaseModel):
    topic_id: int
    topic_name: str
    average_score: float
    student_count: int


class StudentRiskRowResponse(BaseModel):
    user_id: int
    name: str
    email: str
    completion_percent: float
    average_score: float
    risk_level: str
    xp: int


class TeacherAnalyticsResponse(BaseModel):
    tenant_id: int
    student_count: int
    weak_topic_clusters: list[TeacherTopicClusterResponse]
    performance_distribution: dict[str, int]
    top_students: list[StudentRiskRowResponse]
    bottom_students: list[StudentRiskRowResponse]
    risk_students: list[StudentRiskRowResponse]


class ExperimentVariantResponse(BaseModel):
    id: int
    name: str
    population_size: int
    conversion_rate: float
    engagement_lift: float


class ExperimentSummaryItemResponse(BaseModel):
    id: int
    key: str
    name: str
    status: str
    success_metric: str
    variants: list[ExperimentVariantResponse]


class ExperimentSummaryResponse(BaseModel):
    tenant_id: int
    experiments: list[ExperimentSummaryItemResponse]


class CommunityIntelligenceResponse(BaseModel):
    tenant_id: int
    community_count: int
    thread_count: int
    resolved_threads: int
    best_answers: int
    ai_assisted_answers: int


class AdminDashboardResponse(BaseModel):
    tenant_id: int
    total_users: int
    active_learners: int
    roadmap_completions: float
    diagnostics_taken: int
    learners: list[LearnerRoadmapProgressResponse]
