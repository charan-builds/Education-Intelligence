import { apiClient } from "@/services/apiClient";

export type MentorProgressAnalysisResponse = {
  topic_improvements: Record<number, number>;
  weekly_progress: Array<{ week: string; completion_percent: number }>;
  recommended_focus: string[];
};

export async function getMentorProgressAnalysis(): Promise<MentorProgressAnalysisResponse> {
  const { data } = await apiClient.get<MentorProgressAnalysisResponse>("/mentor/progress-analysis");
  return data;
}
