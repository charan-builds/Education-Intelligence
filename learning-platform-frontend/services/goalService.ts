import { apiClient } from "@/services/apiClient";
import type {
  CreateGoalPayload,
  Goal,
  GoalPageResponse,
  GoalTopic,
  GoalTopicPageResponse,
  UpdateGoalPayload,
} from "@/types/goal";

export async function getGoals(): Promise<GoalPageResponse> {
  const { data } = await apiClient.get<GoalPageResponse>("/goals");
  return data;
}

export async function createGoal(payload: CreateGoalPayload): Promise<Goal> {
  const { data } = await apiClient.post<Goal>("/goals", payload);
  return data;
}

export async function updateGoal(goalId: number, payload: UpdateGoalPayload): Promise<Goal> {
  const { data } = await apiClient.put<Goal>(`/goals/${goalId}`, payload);
  return data;
}

export async function deleteGoal(goalId: number): Promise<void> {
  await apiClient.delete(`/goals/${goalId}`);
}

export async function getGoalTopics(goal_id?: number): Promise<GoalTopicPageResponse> {
  const { data } = await apiClient.get<GoalTopicPageResponse>("/goals/topics", {
    params: goal_id ? { goal_id } : undefined,
  });
  return data;
}

export async function createGoalTopic(goal_id: number, topic_id: number): Promise<GoalTopic> {
  const { data } = await apiClient.post<GoalTopic>("/goals/topics", { goal_id, topic_id });
  return data;
}

export async function deleteGoalTopic(linkId: number): Promise<void> {
  await apiClient.delete(`/goals/topics/${linkId}`);
}
