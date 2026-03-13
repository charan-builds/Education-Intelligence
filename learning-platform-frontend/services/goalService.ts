import { apiClient } from "@/services/apiClient";
import type { GoalPageResponse } from "@/types/goal";

export async function getGoals(): Promise<GoalPageResponse> {
  const { data } = await apiClient.get<GoalPageResponse>("/goals");
  return data;
}
