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
import { AUTH_CHANGED_EVENT } from "@/utils/authToken";
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
  login: (email: string, password: string) => Promise<AuthUser | null>;
  logout: () => void;
  refresh: () => void;
  getUser: () => AuthUser | null;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function normalizeUser(payload: ReturnType<typeof getCurrentUser>): AuthUser | null {
  if (!payload) {
    return null;
  }

  const rawUserId = payload.user_id ?? payload.sub;
  const parsedUserId = rawUserId !== undefined && rawUserId !== null ? Number(rawUserId) : null;

  return {
    user_id: Number.isFinite(parsedUserId) ? parsedUserId : null,
    tenant_id: payload.tenant_id !== undefined ? Number(payload.tenant_id) : null,
    role: canonicalizeRole(payload.role ? String(payload.role) : null),
  };
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isReady, setIsReady] = useState(false);

  const refresh = () => {
    startTransition(() => {
      setUser(normalizeUser(getCurrentUser()));
      setIsReady(true);
    });
  };

  useEffect(() => {
    refresh();

    function handleAuthChange() {
      refresh();
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

  const login = async (email: string, password: string) => {
    await loginRequest(email, password);
    const nextUser = normalizeUser(getCurrentUser());
    setUser(nextUser);
    return nextUser;
  };

  const logout = () => {
    logoutRequest();
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("active_tenant_id");
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
