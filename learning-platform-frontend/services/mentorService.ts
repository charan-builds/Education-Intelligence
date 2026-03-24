import { apiClient } from "@/services/apiClient";
import type { MentorChatRequest, MentorChatResponse } from "@/types/mentor";

export async function chatWithMentor(payload: MentorChatRequest): Promise<MentorChatResponse> {
  const { data } = await apiClient.post<MentorChatResponse>("/mentor/chat", payload);
  return data;
}
