"use client";

export const dynamic = "force-dynamic";

import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createTenant, getTenants } from "@/services/tenantService";
import type { TenantType } from "@/types/tenant";

const TENANT_TYPES: TenantType[] = ["platform", "college", "company", "school"];

export default function SuperAdminDashboardPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [type, setType] = useState<TenantType>("school");
  const [formError, setFormError] = useState("");

  const tenantsQuery = useQuery({
    queryKey: ["super-admin-tenants"],
    queryFn: getTenants,
  });

  const tenants = useMemo(() => tenantsQuery.data?.items ?? [], [tenantsQuery.data?.items]);

  const analytics = useMemo(() => {
    const byType: Record<TenantType, number> = {
      platform: 0,
      college: 0,
      company: 0,
      school: 0,
    };

    for (const tenant of tenants) {
      byType[tenant.type] += 1;
    }

    const newest = [...tenants]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 5);

    return {
      total: tenants.length,
      byType,
      newest,
    };
  }, [tenants]);

  const createTenantMutation = useMutation({
    mutationFn: createTenant,
    onSuccess: async () => {
      setName("");
      setType("school");
      setFormError("");
      await queryClient.invalidateQueries({ queryKey: ["super-admin-tenants"] });
    },
    onError: () => {
      setFormError("Failed to create tenant.");
    },
  });

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setFormError("");

    if (!name.trim()) {
      setFormError("Tenant name is required.");
      return;
    }

    await createTenantMutation.mutateAsync({ name: name.trim(), type });
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <h1 className="text-3xl font-semibold tracking-tight">Super Admin Dashboard</h1>
      <p className="mt-2 text-slate-600">Tenant management and platform analytics.</p>

      <section className="mt-8 grid gap-4 md:grid-cols-5">
        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Total Tenants</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">{analytics.total}</p>
        </article>
        {TENANT_TYPES.map((tenantType) => (
          <article key={tenantType} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm capitalize text-slate-500">{tenantType}</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{analytics.byType[tenantType]}</p>
          </article>
        ))}
      </section>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Create Tenant</h2>

        <form className="mt-4 grid gap-4 md:grid-cols-3" onSubmit={onSubmit}>
          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="tenant-name">
              Tenant Name
            </label>
            <input
              id="tenant-name"
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="tenant-type">
              Tenant Type
            </label>
            <select
              id="tenant-type"
              value={type}
              onChange={(event) => setType(event.target.value as TenantType)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
            >
              {TENANT_TYPES.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={createTenantMutation.isPending}
              className="rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {createTenantMutation.isPending ? "Creating..." : "Create Tenant"}
            </button>
          </div>
        </form>

        {formError && <p className="mt-3 text-sm text-red-600">{formError}</p>}
      </section>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Tenant List</h2>

        {tenantsQuery.isLoading && <p className="mt-4 text-slate-600">Loading tenants...</p>}
        {tenantsQuery.isError && <p className="mt-4 text-red-600">Failed to load tenants.</p>}

        {!tenantsQuery.isLoading && !tenantsQuery.isError && tenants.length === 0 && (
          <p className="mt-4 text-slate-600">No tenants found.</p>
        )}

        {tenants.length > 0 && (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">ID</th>
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white text-slate-800">
                {tenants.map((tenant) => (
                  <tr key={tenant.id}>
                    <td className="px-4 py-3">{tenant.id}</td>
                    <td className="px-4 py-3">{tenant.name}</td>
                    <td className="px-4 py-3 capitalize">{tenant.type}</td>
                    <td className="px-4 py-3">{new Date(tenant.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Recent Tenants</h2>
        {analytics.newest.length === 0 ? (
          <p className="mt-4 text-slate-600">No recent tenant data available.</p>
        ) : (
          <ul className="mt-4 space-y-2">
            {analytics.newest.map((tenant) => (
              <li key={tenant.id} className="rounded-lg border border-slate-200 px-4 py-3">
                <p className="font-medium text-slate-900">{tenant.name}</p>
                <p className="text-sm text-slate-600">
                  {tenant.type} • {new Date(tenant.created_at).toLocaleString()}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
