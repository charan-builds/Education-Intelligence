import { apiClient } from "@/services/apiClient";
import type { User } from "@/types/user";
import { clearStoredToken, notifyAuthChanged, setStoredToken } from "@/utils/authToken";

export type AuthSessionResponse = {
  authenticated: boolean;
  token_type: string;
  access_token: string;
  access_token_expires_in: number;
  refresh_token_expires_in?: number | null;
  user: User;
};

export type AuthActionResponse = {
  success: boolean;
  detail: string;
  token?: string | null;
};

export type MFASetupResponse = {
  secret: string;
  otp_auth_url: string;
  manual_entry_code: string;
};

export async function login(
  email: string,
  password: string,
  tenantContext?: { tenant_id?: number | null; tenant_subdomain?: string | null },
  mfa_code?: string | null,
): Promise<AuthSessionResponse> {
  const { data } = await apiClient.post<AuthSessionResponse>("/auth/login", {
    email,
    password,
    tenant_id: tenantContext?.tenant_id ?? undefined,
    tenant_subdomain: tenantContext?.tenant_subdomain ?? undefined,
    mfa_code: mfa_code ?? undefined,
  });
  setStoredToken(data.access_token);
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

export async function acceptInvite(email: string, password: string, invite_token: string): Promise<User> {
  const { data } = await apiClient.post<User>("/auth/invite-accept", {
    email,
    password,
    invite_token,
  });
  return data;
}

export async function requestEmailVerification(tenant_id: number, email: string): Promise<AuthActionResponse> {
  const { data } = await apiClient.post<AuthActionResponse>("/auth/email-verification/request", {
    tenant_id,
    email,
  });
  return data;
}

export async function confirmEmailVerification(token: string): Promise<AuthActionResponse> {
  const { data } = await apiClient.post<AuthActionResponse>("/auth/email-verification", {
    token,
  });
  return data;
}

export async function requestPasswordReset(tenant_id: number, email: string): Promise<AuthActionResponse> {
  const { data } = await apiClient.post<AuthActionResponse>("/auth/forgot-password", {
    tenant_id,
    email,
  });
  return data;
}

export async function confirmPasswordReset(token: string, password: string): Promise<AuthActionResponse> {
  const { data } = await apiClient.post<AuthActionResponse>("/auth/reset-password", {
    token,
    password,
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
    clearStoredToken();
    notifyAuthChanged();
  }
}

export async function setupMfa(): Promise<MFASetupResponse> {
  const { data } = await apiClient.post<MFASetupResponse>("/auth/mfa/setup");
  return data;
}

export async function enableMfa(code: string): Promise<AuthActionResponse> {
  const { data } = await apiClient.post<AuthActionResponse>("/auth/mfa/enable", { code });
  notifyAuthChanged();
  return data;
}

export async function disableMfa(code: string): Promise<AuthActionResponse> {
  const { data } = await apiClient.post<AuthActionResponse>("/auth/mfa/disable", { code });
  clearStoredToken();
  notifyAuthChanged();
  return data;
}
