"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { getCurrentUser, login as loginRequest } from "@/services/authService";

type AuthUser = {
  user_id: number | null;
  tenant_id: number | null;
  role: string | null;
};

type UseAuthResult = {
  isAuthenticated: boolean;
  user: AuthUser | null;
  role: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  getUser: () => AuthUser | null;
};

function normalizeUser(payload: ReturnType<typeof getCurrentUser>): AuthUser | null {
  if (!payload) {
    return null;
  }

  const rawUserId = payload.user_id ?? payload.sub;
  const parsedUserId = rawUserId !== undefined && rawUserId !== null ? Number(rawUserId) : null;

  return {
    user_id: Number.isFinite(parsedUserId) ? parsedUserId : null,
    tenant_id: payload.tenant_id !== undefined ? Number(payload.tenant_id) : null,
    role: payload.role ? String(payload.role) : null,
  };
}

export function useAuth(): UseAuthResult {
  const [user, setUser] = useState<AuthUser | null>(null);

  const getUser = useCallback((): AuthUser | null => {
    const decoded = getCurrentUser();
    return normalizeUser(decoded);
  }, []);

  useEffect(() => {
    setUser(getUser());
  }, [getUser]);

  const login = useCallback(async (email: string, password: string): Promise<void> => {
    await loginRequest(email, password);
    setUser(getUser());
  }, [getUser]);

  const logout = useCallback((): void => {
    localStorage.removeItem("access_token");
    setUser(null);
  }, []);

  const isAuthenticated = useMemo(() => Boolean(user), [user]);
  const role = user?.role ?? null;

  return {
    isAuthenticated,
    user,
    role,
    login,
    logout,
    getUser,
  };
}
