"use client";

import {
  createContext,
  PropsWithChildren,
  startTransition,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { getCurrentUser, login as loginRequest, logout as logoutRequest, type AuthSessionResponse } from "@/services/authService";
import type { User } from "@/types/user";
import { AUTH_CHANGED_EVENT, clearStoredToken } from "@/utils/authToken";
import { canonicalizeRole } from "@/utils/roleRedirect";

export type AuthUser = {
  user_id: number | null;
  tenant_id: number | null;
  role: string | null;
  full_name: string | null;
  email: string | null;
  is_profile_completed: boolean;
  is_email_verified: boolean;
};

type AuthStatus = {
  scope: "onboarding" | "full_access";
  requiresProfileCompletion: boolean;
};

type AuthContextValue = {
  isReady: boolean;
  isAuthenticated: boolean;
  requiresProfileCompletion: boolean;
  scope: "onboarding" | "full_access";
  user: AuthUser | null;
  role: string | null;
  login: (
    email: string,
    password: string,
    tenantContext?: { tenant_id?: number | null; tenant_subdomain?: string | null },
    mfaCode?: string | null,
  ) => Promise<AuthSessionResponse>;
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
    full_name: typeof payload.full_name === "string" ? payload.full_name : null,
    email: payload.email ?? null,
    is_profile_completed: Boolean(payload.is_profile_completed),
    is_email_verified: Boolean(payload.is_email_verified ?? payload.email_verified_at),
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
  const [authStatus, setAuthStatus] = useState<AuthStatus>({
    scope: "full_access",
    requiresProfileCompletion: false,
  });
  const [isReady, setIsReady] = useState(false);
  const authRequestVersionRef = useRef(0);

  const refresh = async () => {
    const requestVersion = ++authRequestVersionRef.current;
    const nextUser = normalizeUser(await getCurrentUser());
    if (requestVersion !== authRequestVersionRef.current) {
      return;
    }
    syncStoredAuthState(nextUser);
    startTransition(() => {
      setUser(nextUser);
      setAuthStatus({
        scope: nextUser?.is_profile_completed === false ? "onboarding" : "full_access",
        requiresProfileCompletion: nextUser?.is_profile_completed === false,
      });
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
    mfaCode?: string | null,
  ) => {
    const requestVersion = ++authRequestVersionRef.current;
    const session = await loginRequest(email, password, tenantContext, mfaCode);
    if (requestVersion !== authRequestVersionRef.current) {
      return session;
    }
    const nextUser = normalizeUser(session.user);
    syncStoredAuthState(nextUser);
    startTransition(() => {
      setUser(nextUser);
      setAuthStatus({
        scope: session.scope,
        requiresProfileCompletion: session.requires_profile_completion,
      });
      setIsReady(true);
    });
    return session;
  };

  const logout = () => {
    authRequestVersionRef.current += 1;
    void logoutRequest();
    if (typeof window !== "undefined") {
      clearStoredToken();
      window.localStorage.removeItem(ACTIVE_TENANT_STORAGE_KEY);
      window.localStorage.removeItem(AUTH_ROLE_STORAGE_KEY);
    }
    startTransition(() => {
      setUser(null);
      setAuthStatus({
        scope: "full_access",
        requiresProfileCompletion: false,
      });
      setIsReady(true);
    });
  };

  const value = useMemo<AuthContextValue>(
    () => ({
      isReady,
      isAuthenticated: Boolean(user),
      requiresProfileCompletion: authStatus.requiresProfileCompletion,
      scope: authStatus.scope,
      user,
      role: user?.role ?? null,
      login,
      logout,
      refresh,
      getUser: () => user,
    }),
    [authStatus, isReady, user],
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
