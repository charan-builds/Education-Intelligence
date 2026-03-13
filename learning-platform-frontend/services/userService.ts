import { apiClient } from "@/services/apiClient";
import type { CreateUserPayload, User, UserPageResponse } from "@/types/user";

export async function getUsers(): Promise<UserPageResponse> {
  const { data } = await apiClient.get<UserPageResponse>("/users");
  return data;
}

export async function createUser(payload: CreateUserPayload): Promise<User> {
  const { data } = await apiClient.post<User>("/users", payload);
  return data;
}
