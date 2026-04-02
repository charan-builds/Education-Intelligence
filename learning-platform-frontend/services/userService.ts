import { apiClient } from "@/services/apiClient";
import type { CompleteUserProfilePayload, CreateUserPayload, UpdateUserProfilePayload, User, UserPageResponse } from "@/types/user";

export async function getUsers(): Promise<UserPageResponse> {
  const { data } = await apiClient.get<UserPageResponse>("/users");
  return data;
}

export async function createUser(payload: CreateUserPayload): Promise<User> {
  const { data } = await apiClient.post<User>("/users", payload);
  return data;
}

export async function getMyProfile(): Promise<User> {
  const { data } = await apiClient.get<User>("/users/me");
  return data;
}

export async function updateMyProfile(payload: UpdateUserProfilePayload): Promise<User> {
  const { data } = await apiClient.patch<User>("/users/me", payload);
  return data;
}

export async function completeMyProfile(payload: CompleteUserProfilePayload): Promise<User> {
  const { data } = await apiClient.put<User>("/users/complete-profile", payload);
  return data;
}
