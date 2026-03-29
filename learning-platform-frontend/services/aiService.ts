import { apiClient } from "@/services/apiClient";
import type { AIChatHistoryItem, AIChatRequest, AIChatResponse } from "@/types/ai";

export async function getAIChatHistory(): Promise<AIChatHistoryItem[]> {
  const { data } = await apiClient.get<AIChatHistoryItem[]>("/ai/chat");
  return data;
}

export async function sendAIChatMessage(payload: AIChatRequest): Promise<AIChatResponse> {
  const { data } = await apiClient.post<AIChatResponse>("/ai/chat", payload);
  return data;
}
