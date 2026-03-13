import { apiClient } from "@/services/apiClient";

export type MentorChatRequest = {
  message: string;
  user_id: number;
  tenant_id: number;
};

export type MentorChatResponse = {
  reply: string;
  advisor_type: string;
};

export async function chatWithMentor(payload: MentorChatRequest): Promise<MentorChatResponse> {
  const { data } = await apiClient.post<MentorChatResponse>("/mentor/chat", payload);
  return data;
}
