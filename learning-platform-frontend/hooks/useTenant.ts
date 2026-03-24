"use client";

import { useMemo } from "react";

import { useAuth } from "@/hooks/useAuth";
import { useTenantScope } from "@/hooks/useTenantScope";

export function useTenant() {
  const { user } = useAuth();
  const { activeTenantScope, setActiveTenantScope, clearActiveTenantScope } = useTenantScope();

  return useMemo(
    () => ({
      activeTenantScope,
      setActiveTenantScope,
      clearActiveTenantScope,
      effectiveTenantId: activeTenantScope ? Number(activeTenantScope) : user?.tenant_id ?? null,
      actorTenantId: user?.tenant_id ?? null,
    }),
    [activeTenantScope, clearActiveTenantScope, setActiveTenantScope, user?.tenant_id],
  );
}
