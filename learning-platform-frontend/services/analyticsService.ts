import { apiClient } from "@/services/apiClient";
import type {
  AnalyticsOverview,
  LearnerIntelligenceOverview,
  LearnerSkillVectorResponse,
  LearningTrendPoint,
  PlatformAnalyticsOverview,
  RetentionAnalytics,
  RoadmapProgressSummary,
  WeakTopicInsight,
  TopicMasteryDistribution,
} from "@/types/analytics";

export async function getAnalyticsOverview(): Promise<AnalyticsOverview> {
  const { data } = await apiClient.get<AnalyticsOverview>("/analytics/overview");
  return data;
}

export async function getRoadmapProgressSummary(): Promise<RoadmapProgressSummary> {
  const { data } = await apiClient.get<RoadmapProgressSummary>("/analytics/roadmap-progress");
  return data;
}

export async function getTopicMasteryAnalytics(): Promise<{
  tenant_id: number;
  topic_mastery_distribution: TopicMasteryDistribution;
}> {
  const { data } = await apiClient.get<{
    tenant_id: number;
    topic_mastery_distribution: TopicMasteryDistribution;
  }>("/analytics/topic-mastery");
  return data;
}

export async function getPlatformAnalyticsOverview(): Promise<PlatformAnalyticsOverview> {
  const { data } = await apiClient.get<PlatformAnalyticsOverview>("/analytics/platform-overview");
  return data;
}

export async function getRetentionAnalytics(): Promise<RetentionAnalytics> {
  const { data } = await apiClient.get<RetentionAnalytics>("/analytics/retention");
  return data;
}

export async function getStudentInsights(): Promise<LearnerIntelligenceOverview> {
  const { data } = await apiClient.get<LearnerIntelligenceOverview>("/analytics/student-insights");
  return data;
}

export async function getSkillVectors(): Promise<LearnerSkillVectorResponse> {
  const { data } = await apiClient.get<LearnerSkillVectorResponse>("/analytics/skill-vectors");
  return data;
}

export async function getWeakTopics(): Promise<WeakTopicInsight[]> {
  const { data } = await apiClient.get<WeakTopicInsight[]>("/analytics/weak-topics");
  return data;
}

export async function getLearningTrends(): Promise<LearningTrendPoint[]> {
  const { data } = await apiClient.get<LearningTrendPoint[]>("/analytics/learning-trends");
  return data;
}
