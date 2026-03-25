from pydantic import BaseModel

from app.schemas.common_schema import PageMeta


class TopicMasteryDistributionResponse(BaseModel):
    beginner: int
    needs_practice: int
    mastered: int


class AnalyticsOverviewResponse(BaseModel):
    tenant_id: int
    topic_mastery_distribution: TopicMasteryDistributionResponse
    diagnostic_completion_rate: float
    roadmap_completion_rate: float


class LearnerRoadmapProgressResponse(BaseModel):
    user_id: int
    email: str
    total_steps: int
    completed_steps: int
    in_progress_steps: int
    pending_steps: int
    completion_percent: int
    mastery_percent: int


class RoadmapProgressSummaryResponse(BaseModel):
    tenant_id: int
    student_count: int
    average_completion_percent: int
    average_mastery_percent: int
    learners: list[LearnerRoadmapProgressResponse]
    meta: PageMeta


class TopicMasteryAnalyticsResponse(BaseModel):
    tenant_id: int
    topic_mastery_distribution: TopicMasteryDistributionResponse


class TenantAnalyticsSummaryResponse(BaseModel):
    tenant_id: int
    tenant_name: str
    tenant_type: str
    student_count: int
    mentor_count: int
    teacher_count: int
    admin_count: int
    super_admin_count: int
    diagnostic_completion_rate: float
    roadmap_completion_rate: float
    average_completion_percent: int
    average_mastery_percent: int


class PlatformAnalyticsOverviewResponse(BaseModel):
    tenant_count: int
    student_count: int
    mentor_count: int
    teacher_count: int
    admin_count: int
    super_admin_count: int
    diagnostic_completion_rate: float
    roadmap_completion_rate: float
    average_completion_percent: int
    average_mastery_percent: int
    topic_mastery_distribution: TopicMasteryDistributionResponse
    tenant_breakdown: list[TenantAnalyticsSummaryResponse]


class RetentionCurvePointResponse(BaseModel):
    label: str
    engagement_events: int
    average_retention_score: float


class WeakRetentionTopicResponse(BaseModel):
    topic_name: str
    average_retention_score: float
    learner_count: int


class RetentionAnalyticsResponse(BaseModel):
    tenant_id: int
    due_review_count: int
    retention_curve: list[RetentionCurvePointResponse]
    weak_retention_topics: list[WeakRetentionTopicResponse]


class SkillVectorItemResponse(BaseModel):
    topic_id: int
    topic_name: str
    mastery_score: float
    confidence_score: float
    last_updated: str


class WeakTopicInsightResponse(BaseModel):
    topic_id: int
    topic_name: str
    mastery_score: float
    confidence_score: float


class LearningTrendPointResponse(BaseModel):
    label: str
    events: int
    minutes_spent: float
    completions: int
    retries: int


class LearnerIntelligenceOverviewResponse(BaseModel):
    tenant_id: int
    user_id: int
    mastery_avg: float
    confidence_avg: float
    learning_speed_seconds: float
    retry_count: int
    tracked_topics: int


class LearnerSkillVectorResponse(BaseModel):
    tenant_id: int
    user_id: int
    vectors: list[SkillVectorItemResponse]
