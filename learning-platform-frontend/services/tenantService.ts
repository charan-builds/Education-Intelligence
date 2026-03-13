import { apiClient } from "@/services/apiClient";
import type { CreateTenantPayload, Tenant, TenantPageResponse } from "@/types/tenant";

export async function getTenants(): Promise<TenantPageResponse> {
  const { data } = await apiClient.get<TenantPageResponse>("/tenants");
  return data;
}

export async function createTenant(payload: CreateTenantPayload): Promise<Tenant> {
  const { data } = await apiClient.post<Tenant>("/tenants", payload);
  return data;
}
