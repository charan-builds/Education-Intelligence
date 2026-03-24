"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import PageHeader from "@/components/layouts/PageHeader";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/components/providers/ToastProvider";
import Button from "@/components/ui/Button";
import Select from "@/components/ui/Select";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { getFeatureFlagCatalog, getFeatureFlags, updateFeatureFlag } from "@/services/opsService";
import { getTenants } from "@/services/tenantService";

export default function AdminFeatureFlagsPage() {
  const { role, user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [selectedTenantId, setSelectedTenantId] = useState<string>(String(user?.tenant_id ?? ""));

  const tenantScope = role === "super_admin" ? Number(selectedTenantId) || undefined : undefined;

  const flagsQuery = useQuery({
    queryKey: ["admin", "feature-flags", tenantScope],
    queryFn: () => getFeatureFlags({ tenant_id: tenantScope, limit: 50, offset: 0 }),
  });
  const catalogQuery = useQuery({
    queryKey: ["admin", "feature-flags", "catalog"],
    queryFn: getFeatureFlagCatalog,
  });
  const tenantsQuery = useQuery({
    queryKey: ["admin", "feature-flags", "tenants"],
    queryFn: getTenants,
    enabled: role === "super_admin",
  });

  const updateMutation = useMutation({
    mutationFn: ({ flagName, enabled }: { flagName: string; enabled: boolean }) =>
      updateFeatureFlag(flagName, { enabled, tenant_id: tenantScope }),
    onSuccess: async () => {
      toast({ title: "Feature flag updated", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["admin", "feature-flags"] });
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin"
        title="Feature flags"
        description="Control tenant capabilities with backend-backed feature flags. Super admins can target another tenant."
      />

      {role === "super_admin" ? (
        <SurfaceCard title="Tenant scope" description="Choose which tenant receives the feature-flag update.">
          <Select value={selectedTenantId} onChange={(event) => setSelectedTenantId(event.target.value)}>
            {(tenantsQuery.data?.items ?? []).map((tenant) => (
              <option key={tenant.id} value={tenant.id}>
                {tenant.name}
              </option>
            ))}
          </Select>
        </SurfaceCard>
      ) : null}

      <SurfaceCard title="Feature flag catalog" description="Every supported flag and its current tenant state.">
        <div className="space-y-3">
          {(catalogQuery.data?.items ?? []).map((flagName) => {
            const currentFlag = (flagsQuery.data?.items ?? []).find((item) => item.feature_name === flagName);
            return (
              <div
                key={flagName}
                className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{flagName}</p>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                      Current state: {currentFlag?.enabled ? "enabled" : "disabled"}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant={currentFlag?.enabled ? "secondary" : "primary"}
                      onClick={() => updateMutation.mutate({ flagName, enabled: true })}
                      disabled={updateMutation.isPending}
                    >
                      Enable
                    </Button>
                    <Button
                      variant={currentFlag?.enabled ? "danger" : "ghost"}
                      onClick={() => updateMutation.mutate({ flagName, enabled: false })}
                      disabled={updateMutation.isPending}
                    >
                      Disable
                    </Button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </SurfaceCard>
    </div>
  );
}
