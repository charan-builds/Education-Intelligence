import { apiClient } from "@/services/apiClient";
import type { User } from "@/types/user";
import { notifyAuthChanged } from "@/utils/authToken";

export type AuthSessionResponse = {
  authenticated: boolean;
  token_type: string;
  access_token_expires_in: number;
  refresh_token_expires_in?: number | null;
  user: User;
};

export async function login(
  email: string,
  password: string,
  tenantContext?: { tenant_id?: number | null; tenant_subdomain?: string | null },
): Promise<AuthSessionResponse> {
  const { data } = await apiClient.post<AuthSessionResponse>("/auth/login", {
    email,
    password,
    tenant_id: tenantContext?.tenant_id ?? undefined,
    tenant_subdomain: tenantContext?.tenant_subdomain ?? undefined,
  });
  notifyAuthChanged();
  return data;
}

export async function register(email: string, password: string, invite_token?: string | null): Promise<User> {
  const { data } = await apiClient.post<User>("/auth/register", {
    email,
    password,
    invite_token,
  });
  return data;
}

export async function getCurrentUser(): Promise<User | null> {
  try {
    const { data } = await apiClient.get<User>("/users/me");
    return data;
  } catch {
    return null;
  }
}

export async function logout(): Promise<void> {
  try {
    await apiClient.post("/auth/logout");
  } finally {
    notifyAuthChanged();
  }
}
