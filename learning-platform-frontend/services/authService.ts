import { jwtDecode } from "jwt-decode";

import { apiClient } from "@/services/apiClient";
import type { User } from "@/types/user";
import { clearAccessToken, getAccessToken, storeAccessToken } from "@/utils/authToken";

export type AuthTokenResponse = {
  access_token: string;
  token_type?: string;
};

export type CurrentUser = {
  sub?: string;
  tenant_id?: number;
  role?: string;
  exp?: number;
  [key: string]: unknown;
};

export async function login(email: string, password: string): Promise<AuthTokenResponse> {
  const { data } = await apiClient.post<AuthTokenResponse>("/auth/login", {
    email,
    password,
  });

  if (data.access_token) {
    storeAccessToken(data.access_token);
  }

  return data;
}

export async function register(
  email: string,
  password: string,
  tenant_id: number,
  role: string,
): Promise<User> {
  const { data } = await apiClient.post<User>("/auth/register", {
    email,
    password,
    tenant_id,
    role,
  });
  return data;
}

export function getCurrentUser(): CurrentUser | null {
  if (typeof window === "undefined") {
    return null;
  }

  const token = getAccessToken();
  if (!token) {
    return null;
  }

  try {
    return jwtDecode<CurrentUser>(token);
  } catch {
    return null;
  }
}

export function logout(): void {
  clearAccessToken();
}
