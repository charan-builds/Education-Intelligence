import { apiClient } from "@/services/apiClient";
import type { Roadmap, RoadmapPageResponse, RoadmapStep, UpdateRoadmapStepPayload } from "@/types/roadmap";

export async function generateRoadmap(goal_id: number, test_id: number): Promise<Roadmap> {
  const { data } = await apiClient.post<Roadmap>("/roadmap/generate", {
    goal_id,
    test_id,
  });
  return data;
}

export async function getUserRoadmap(user_id: number): Promise<RoadmapPageResponse> {
  const { data } = await apiClient.get<RoadmapPageResponse>(`/roadmap/${user_id}`);
  return data;
}

export async function getCurrentRoadmapPage(): Promise<RoadmapPageResponse> {
  const { data } = await apiClient.get<RoadmapPageResponse>("/roadmap/view");
  return data;
}

export async function getLatestRoadmap(user_id: number): Promise<Roadmap | null> {
  const data = await getUserRoadmap(user_id);
  return data.items[0] ?? null;
}

export async function updateRoadmapStep(step_id: number, payload: UpdateRoadmapStepPayload): Promise<RoadmapStep> {
  const { data } = await apiClient.patch<RoadmapStep>(`/roadmap/steps/${step_id}`, payload);
  return data;
}
