import { apiClient } from "@/services/apiClient";
import type { SocialNetworkResponse } from "@/types/social";

export async function getSocialNetwork(): Promise<SocialNetworkResponse> {
  const { data } = await apiClient.get<SocialNetworkResponse>("/social/network");
  return data;
}

export async function followUser(userId: number): Promise<void> {
  await apiClient.post("/social/follows", { user_id: userId });
}

export async function unfollowUser(userId: number): Promise<void> {
  await apiClient.delete(`/social/follows/${userId}`);
}
