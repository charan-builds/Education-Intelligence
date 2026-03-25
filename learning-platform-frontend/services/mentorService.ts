import { apiClient } from "@/services/apiClient";
import type {
  HybridMentorshipOverview,
  HybridSessionPlanRequest,
  HybridSessionPlanResponse,
  MentorChatRequest,
  MentorChatResponse,
} from "@/types/mentor";

export async function chatWithMentor(payload: MentorChatRequest): Promise<MentorChatResponse> {
  const { data } = await apiClient.post<MentorChatResponse>("/mentor/chat", payload);
  return data;
}

export async function getHybridMentorNetwork(learnerId?: number): Promise<HybridMentorshipOverview> {
  const { data } = await apiClient.get<HybridMentorshipOverview>("/mentor/hybrid-network", {
    params: learnerId ? { learner_id: learnerId } : undefined,
  });
  return data;
}

export async function buildHybridSessionPlan(payload: HybridSessionPlanRequest): Promise<HybridSessionPlanResponse> {
  const { data } = await apiClient.post<HybridSessionPlanResponse>("/mentor/hybrid-network/session-plan", payload);
  return data;
}
