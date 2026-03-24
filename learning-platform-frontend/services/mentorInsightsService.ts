import { apiClient } from "@/services/apiClient";
import type {
  AutonomousAgentResponse,
  MentorNotificationsResponse,
  MentorProgressAnalysisResponse,
  MentorSuggestionsResponse,
} from "@/types/mentor";

export async function getMentorSuggestions(): Promise<MentorSuggestionsResponse> {
  const { data } = await apiClient.get<MentorSuggestionsResponse>("/mentor/suggestions");
  return data;
}

export async function getMentorProgressAnalysis(): Promise<MentorProgressAnalysisResponse> {
  const { data } = await apiClient.get<MentorProgressAnalysisResponse>("/mentor/progress-analysis");
  return data;
}

export async function getMentorNotifications(): Promise<MentorNotificationsResponse> {
  const { data } = await apiClient.get<MentorNotificationsResponse>("/mentor/notifications");
  return data;
}

export async function getAutonomousAgentStatus(): Promise<AutonomousAgentResponse> {
  const { data } = await apiClient.get<AutonomousAgentResponse>("/mentor/agent/status");
  return data;
}

export async function runAutonomousAgent(): Promise<AutonomousAgentResponse> {
  const { data } = await apiClient.post<AutonomousAgentResponse>("/mentor/agent/run");
  return data;
}
