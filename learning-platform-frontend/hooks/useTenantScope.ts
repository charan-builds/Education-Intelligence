"use client";

import { useTenantContext } from "@/components/providers/TenantProvider";

export function useTenantScope() {
  return useTenantContext();
}
