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

const TENANT_SCOPE_EVENT = "tenant-scope-changed";
const STORAGE_KEY = "active_tenant_id";

type TenantContextValue = {
  activeTenantScope: string | null;
  setActiveTenantScope: (tenantId: string | null) => void;
  clearActiveTenantScope: () => void;
};

const TenantContext = createContext<TenantContextValue | null>(null);

function readTenantScope(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(STORAGE_KEY);
}

function emitTenantScopeChanged(): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(TENANT_SCOPE_EVENT));
  }
}

export function TenantProvider({ children }: PropsWithChildren) {
  const [activeTenantScope, setActiveTenantScopeState] = useState<string | null>(null);

  useEffect(() => {
    startTransition(() => {
      setActiveTenantScopeState(readTenantScope());
    });

    function syncTenantScope(): void {
      setActiveTenantScopeState(readTenantScope());
    }

    if (typeof window === "undefined") {
      return;
    }

    window.addEventListener(TENANT_SCOPE_EVENT, syncTenantScope);
    window.addEventListener("storage", syncTenantScope);
    return () => {
      window.removeEventListener(TENANT_SCOPE_EVENT, syncTenantScope);
      window.removeEventListener("storage", syncTenantScope);
    };
  }, []);

  const setActiveTenantScope = (tenantId: string | null) => {
    if (typeof window === "undefined") {
      return;
    }

    if (!tenantId || tenantId === "current") {
      window.localStorage.removeItem(STORAGE_KEY);
    } else {
      window.localStorage.setItem(STORAGE_KEY, tenantId);
    }

    emitTenantScopeChanged();
    startTransition(() => {
      setActiveTenantScopeState(readTenantScope());
    });
  };

  const contextValue = useMemo<TenantContextValue>(
    () => ({
      activeTenantScope,
      setActiveTenantScope,
      clearActiveTenantScope: () => setActiveTenantScope(null),
    }),
    [activeTenantScope],
  );

  return <TenantContext.Provider value={contextValue}>{children}</TenantContext.Provider>;
}

export function useTenantContext() {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error("useTenantContext must be used within TenantProvider");
  }
  return context;
}

export { TENANT_SCOPE_EVENT };
