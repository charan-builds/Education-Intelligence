"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import PageHeader from "@/components/layouts/PageHeader";
import { useTenant } from "@/hooks/useTenant";
import { useToast } from "@/components/providers/ToastProvider";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { createTenant, getTenants } from "@/services/tenantService";
import type { TenantType } from "@/types/tenant";
import { describeTenantAudience, formatTenantTypeLabel } from "@/utils/tenantLabels";

const TENANT_TYPES: TenantType[] = ["platform", "college", "company", "school", "personal"];

export default function SuperAdminTenantsPage() {
  const { toast } = useToast();
  const { activeTenantScope, setActiveTenantScope } = useTenant();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [type, setType] = useState<TenantType>("school");

  const tenantsQuery = useQuery({
    queryKey: ["super-admin", "tenants"],
    queryFn: getTenants,
  });

  const createMutation = useMutation({
    mutationFn: createTenant,
    onSuccess: async () => {
      setName("");
      setType("school");
      toast({ title: "Tenant created", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["super-admin", "tenants"] });
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Super admin"
        title="Tenant management"
        description="Create institution tenants or personal learner workspaces and switch into cross-tenant inspection mode."
      />

      <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
        <SurfaceCard title="Create tenant" description="Provision a new institution tenant or a self-serve learner workspace.">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              createMutation.mutate({ name, type });
            }}
          >
            <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Tenant name" required />
            <Select value={type} onChange={(event) => setType(event.target.value as TenantType)}>
              {TENANT_TYPES.map((item) => (
                <option key={item} value={item}>
                  {formatTenantTypeLabel(item)}
                </option>
              ))}
            </Select>
            <p className="text-sm text-slate-600 dark:text-slate-400">{describeTenantAudience(type)}</p>
            <Button type="submit">Create tenant</Button>
          </form>
        </SurfaceCard>

        <SurfaceCard title="Tenant list" description="Use inspection mode to view institution tenants and personal learner workspaces without changing your login.">
          <div className="space-y-3">
            {(tenantsQuery.data?.items ?? []).map((tenant) => (
              <div
                key={tenant.id}
                className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
              >
                <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{tenant.name}</p>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                      {formatTenantTypeLabel(tenant.type)} • {describeTenantAudience(tenant.type)}
                    </p>
                    <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                      subdomain {tenant.subdomain ?? "not-set"} • created {new Date(tenant.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Button
                    variant={activeTenantScope === String(tenant.id) ? "secondary" : "primary"}
                    onClick={() => setActiveTenantScope(String(tenant.id))}
                  >
                    {activeTenantScope === String(tenant.id) ? "Inspecting" : "Inspect tenant"}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}
