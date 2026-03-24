export type LearnerRoadmapProgress = {
  user_id: number;
  email: string;
  total_steps: number;
  completed_steps: number;
  in_progress_steps: number;
  pending_steps: number;
  completion_percent: number;
  mastery_percent: number;
};

export type RoadmapProgressSummary = {
  tenant_id: number;
  student_count: number;
  average_completion_percent: number;
  average_mastery_percent: number;
  learners: LearnerRoadmapProgress[];
};

export type TopicMasteryDistribution = {
  beginner: number;
  needs_practice: number;
  mastered: number;
};

export type AnalyticsOverview = {
  tenant_id: number;
  topic_mastery_distribution: TopicMasteryDistribution;
  diagnostic_completion_rate: number;
  roadmap_completion_rate: number;
};

export type TenantAnalyticsSummary = {
  tenant_id: number;
  tenant_name: string;
  tenant_type: string;
  student_count: number;
  mentor_count: number;
  teacher_count: number;
  admin_count: number;
  super_admin_count: number;
  diagnostic_completion_rate: number;
  roadmap_completion_rate: number;
  average_completion_percent: number;
  average_mastery_percent: number;
};

export type PlatformAnalyticsOverview = {
  tenant_count: number;
  student_count: number;
  mentor_count: number;
  teacher_count: number;
  admin_count: number;
  super_admin_count: number;
  diagnostic_completion_rate: number;
  roadmap_completion_rate: number;
  average_completion_percent: number;
  average_mastery_percent: number;
  topic_mastery_distribution: TopicMasteryDistribution;
  tenant_breakdown: TenantAnalyticsSummary[];
};

export type RetentionCurvePoint = {
  label: string;
  engagement_events: number;
  average_retention_score: number;
};

export type WeakRetentionTopic = {
  topic_name: string;
  average_retention_score: number;
  learner_count: number;
};

export type RetentionAnalytics = {
  tenant_id: number;
  due_review_count: number;
  retention_curve: RetentionCurvePoint[];
  weak_retention_topics: WeakRetentionTopic[];
};
