import { jwtDecode } from "jwt-decode";

import { apiClient } from "@/services/apiClient";

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

  if (typeof window !== "undefined" && data.access_token) {
    localStorage.setItem("access_token", data.access_token);
  }

  return data;
}

export async function register(
  email: string,
  password: string,
  tenant_id: number,
  role: string,
): Promise<AuthTokenResponse> {
  const { data } = await apiClient.post<AuthTokenResponse>("/auth/register", {
    email,
    password,
    tenant_id,
    role,
  });

  if (typeof window !== "undefined" && data.access_token) {
    localStorage.setItem("access_token", data.access_token);
  }

  return data;
}

export function getCurrentUser(): CurrentUser | null {
  if (typeof window === "undefined") {
    return null;
  }

  const token = localStorage.getItem("access_token");
  if (!token) {
    return null;
  }

  try {
    return jwtDecode<CurrentUser>(token);
  } catch {
    return null;
  }
}
