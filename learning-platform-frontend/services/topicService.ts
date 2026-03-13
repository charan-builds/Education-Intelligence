import { apiClient } from "@/services/apiClient";
import type { TopicDetail } from "@/types/topic";

export async function getTopic(topicId: number): Promise<TopicDetail> {
  const { data } = await apiClient.get<TopicDetail>(`/topics/${topicId}`);
  return data;
}
