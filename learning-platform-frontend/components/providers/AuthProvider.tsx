"use client";

import {
  createContext,
  PropsWithChildren,
  startTransition,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { getCurrentUser, login as loginRequest, logout as logoutRequest } from "@/services/authService";
import type { User } from "@/types/user";
import { AUTH_CHANGED_EVENT, clearStoredToken } from "@/utils/authToken";
import { canonicalizeRole } from "@/utils/roleRedirect";

export type AuthUser = {
  user_id: number | null;
  tenant_id: number | null;
  role: string | null;
};

type AuthContextValue = {
  isReady: boolean;
  isAuthenticated: boolean;
  user: AuthUser | null;
  role: string | null;
  login: (
    email: string,
    password: string,
    tenantContext?: { tenant_id?: number | null; tenant_subdomain?: string | null },
  ) => Promise<AuthUser | null>;
  logout: () => void;
  refresh: () => Promise<void>;
  getUser: () => AuthUser | null;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const ACTIVE_TENANT_STORAGE_KEY = "active_tenant_id";
const AUTH_ROLE_STORAGE_KEY = "auth_user_role";

function normalizeUser(payload: User | null): AuthUser | null {
  if (!payload) {
    return null;
  }

  return {
    user_id: Number.isFinite(payload.id) ? payload.id : null,
    tenant_id: Number.isFinite(payload.tenant_id) ? payload.tenant_id : null,
    role: canonicalizeRole(payload.role ? String(payload.role) : null),
  };
}

function syncStoredAuthState(user: AuthUser | null): void {
  if (typeof window === "undefined") {
    return;
  }
  if (!user?.role) {
    window.localStorage.removeItem(AUTH_ROLE_STORAGE_KEY);
    window.localStorage.removeItem(ACTIVE_TENANT_STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(AUTH_ROLE_STORAGE_KEY, user.role);
  if (user.role !== "super_admin") {
    window.localStorage.removeItem(ACTIVE_TENANT_STORAGE_KEY);
  }
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isReady, setIsReady] = useState(false);

  const refresh = async () => {
    const nextUser = normalizeUser(await getCurrentUser());
    syncStoredAuthState(nextUser);
    startTransition(() => {
      setUser(nextUser);
      setIsReady(true);
    });
  };

  useEffect(() => {
    void refresh();

    function handleAuthChange() {
      void refresh();
    }

    if (typeof window === "undefined") {
      return;
    }

    window.addEventListener(AUTH_CHANGED_EVENT, handleAuthChange);
    window.addEventListener("storage", handleAuthChange);
    return () => {
      window.removeEventListener(AUTH_CHANGED_EVENT, handleAuthChange);
      window.removeEventListener("storage", handleAuthChange);
    };
  }, []);

  const login = async (
    email: string,
    password: string,
    tenantContext?: { tenant_id?: number | null; tenant_subdomain?: string | null },
  ) => {
    const session = await loginRequest(email, password, tenantContext);
    const nextUser = normalizeUser(session.user);
    syncStoredAuthState(nextUser);
    setUser(nextUser);
    return nextUser;
  };

  const logout = () => {
    void logoutRequest();
    if (typeof window !== "undefined") {
      clearStoredToken();
      window.localStorage.removeItem(ACTIVE_TENANT_STORAGE_KEY);
      window.localStorage.removeItem(AUTH_ROLE_STORAGE_KEY);
    }
    setUser(null);
  };

  const value = useMemo<AuthContextValue>(
    () => ({
      isReady,
      isAuthenticated: Boolean(user),
      user,
      role: user?.role ?? null,
      login,
      logout,
      refresh,
      getUser: () => user,
    }),
    [isReady, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used within AuthProvider");
  }
  return context;
}
