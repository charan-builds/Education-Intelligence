"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Code2, Layers3, ShoppingBag, Wallet } from "lucide-react";
import { useState } from "react";

import PageHeader from "@/components/layouts/PageHeader";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import {
  assignSubscription,
  createApiClient,
  createPlugin,
  createSubscriptionPlan,
  getApiClients,
  getEcosystemOverview,
  getMarketplaceListings,
  getPlugins,
  getSubscriptionPlans,
} from "@/services/ecosystemService";

export default function AdminEcosystemPage() {
  const queryClient = useQueryClient();
  const [pluginName, setPluginName] = useState("");
  const [apiClientName, setApiClientName] = useState("");
  const [planName, setPlanName] = useState("");

  const overviewQuery = useQuery({ queryKey: ["ecosystem", "overview"], queryFn: getEcosystemOverview });
  const marketplaceQuery = useQuery({ queryKey: ["ecosystem", "marketplace"], queryFn: getMarketplaceListings });
  const pluginsQuery = useQuery({ queryKey: ["ecosystem", "plugins"], queryFn: getPlugins });
  const apiClientsQuery = useQuery({ queryKey: ["ecosystem", "api-clients"], queryFn: getApiClients });
  const plansQuery = useQuery({ queryKey: ["ecosystem", "plans"], queryFn: getSubscriptionPlans });

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["ecosystem"] });
  };

  const createPluginMutation = useMutation({
    mutationFn: () =>
      createPlugin({
        key: pluginName.toLowerCase().replaceAll(/\s+/g, "-") || "new-plugin",
        name: pluginName || "New Plugin",
        plugin_type: "analytics",
        provider: "tenant-extension",
        version: "1.0.0",
        config_json: "{\"mode\":\"managed\"}",
      }),
    onSuccess: refresh,
  });

  const createApiClientMutation = useMutation({
    mutationFn: () =>
      createApiClient({
        name: apiClientName || "Partner App",
        scopes: ["topics:read", "analytics:read", "mentor:write"],
        rate_limit_per_minute: 240,
      }),
    onSuccess: refresh,
  });

  const createPlanMutation = useMutation({
    mutationFn: () =>
      createSubscriptionPlan({
        code: (planName || "growth").toLowerCase().replaceAll(/\s+/g, "-"),
        name: planName || "Growth",
        monthly_price_cents: 19900,
        usage_price_cents: 2,
        features: ["Marketplace access", "Plugin registry", "Public API", "Premium AI"],
      }),
    onSuccess: refresh,
  });

  const activatePlanMutation = useMutation({
    mutationFn: async () => {
      const firstPlan = plansQuery.data?.[0];
      if (!firstPlan) {
        throw new Error("No plan available");
      }
      return assignSubscription({ plan_id: firstPlan.id, seats: 50 });
    },
    onSuccess: refresh,
  });

  const overview = overviewQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Ecosystem"
        title="Turn the product into a platform business"
        description="Operate marketplace supply, plugin extensibility, public APIs, and monetization from one ecosystem control plane."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Marketplace listings" value={overview?.marketplace_listing_count ?? 0} tone="info" icon={<ShoppingBag className="h-5 w-5" />} />
        <MetricCard title="Plugins" value={overview?.plugin_count ?? 0} tone="success" icon={<Layers3 className="h-5 w-5" />} />
        <MetricCard title="API clients" value={overview?.api_client_count ?? 0} tone="warning" icon={<Code2 className="h-5 w-5" />} />
        <MetricCard
          title="MRR"
          value={`$${(((overview?.monetization_snapshot.subscription_mrr_cents ?? 0) / 100)).toFixed(0)}`}
          icon={<Wallet className="h-5 w-5" />}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <SurfaceCard title="Marketplace" description="Teacher-created inventory that makes the platform a supply-side ecosystem.">
          <div className="space-y-3">
            {(marketplaceQuery.data ?? []).slice(0, 4).map((listing) => (
              <div key={listing.id} className="story-card">
                <p className="text-sm font-semibold text-slate-950">{listing.title}</p>
                <p className="mt-2 text-sm leading-7 text-slate-600">{listing.summary}</p>
                <p className="mt-3 text-xs uppercase tracking-[0.18em] text-slate-500">
                  {listing.listing_type} • ${(listing.price_cents / 100).toFixed(2)} • {listing.average_rating.toFixed(1)} stars
                </p>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard title="Monetization" description="Subscription and usage-based revenue levers.">
          <div className="grid gap-3 md:grid-cols-2">
            <div className="story-card">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Active plan</p>
              <p className="mt-3 text-2xl font-semibold text-slate-950">{overview?.monetization_snapshot.active_plan ?? "None"}</p>
              <p className="mt-2 text-sm text-slate-600">Usage units: {overview?.active_subscription?.monthly_usage_units ?? 0}</p>
            </div>
            <div className="story-card">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Marketplace GMV</p>
              <p className="mt-3 text-2xl font-semibold text-slate-950">
                ${(((overview?.monetization_snapshot.marketplace_gmv_cents ?? 0) / 100)).toFixed(0)}
              </p>
              <p className="mt-2 text-sm text-slate-600">Published catalog monetization potential.</p>
            </div>
          </div>
        </SurfaceCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <SurfaceCard title="Plugin Registry" description="Install new recommendation engines, AI providers, and analytics adapters.">
          <div className="space-y-3">
            <input
              value={pluginName}
              onChange={(event) => setPluginName(event.target.value)}
              placeholder="Plugin name"
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm"
            />
            <button
              type="button"
              onClick={() => createPluginMutation.mutate()}
              className="rounded-2xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white"
            >
              Register plugin
            </button>
            {(pluginsQuery.data ?? []).map((plugin) => (
              <div key={plugin.id} className="story-card">
                <p className="text-sm font-semibold text-slate-950">{plugin.name}</p>
                <p className="mt-2 text-sm text-slate-600">{plugin.plugin_type} • {plugin.provider} • v{plugin.version}</p>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard title="API Platform" description="Provision public API credentials for external apps and partners.">
          <div className="space-y-3">
            <input
              value={apiClientName}
              onChange={(event) => setApiClientName(event.target.value)}
              placeholder="Client app name"
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm"
            />
            <button
              type="button"
              onClick={() => createApiClientMutation.mutate()}
              className="rounded-2xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white"
            >
              Create API client
            </button>
            {(apiClientsQuery.data ?? []).map((client) => (
              <div key={client.id} className="story-card">
                <p className="text-sm font-semibold text-slate-950">{client.name}</p>
                <p className="mt-2 break-all text-sm text-slate-600">{client.client_key}</p>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard title="Subscriptions" description="Package premium capability into plans and activate tenant monetization.">
          <div className="space-y-3">
            <input
              value={planName}
              onChange={(event) => setPlanName(event.target.value)}
              placeholder="Plan name"
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm"
            />
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => createPlanMutation.mutate()}
                className="rounded-2xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white"
              >
                Create plan
              </button>
              <button
                type="button"
                onClick={() => activatePlanMutation.mutate()}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-900"
              >
                Activate first plan
              </button>
            </div>
            {(plansQuery.data ?? []).map((plan) => (
              <div key={plan.id} className="story-card">
                <p className="text-sm font-semibold text-slate-950">{plan.name}</p>
                <p className="mt-2 text-sm text-slate-600">
                  ${(plan.monthly_price_cents / 100).toFixed(0)}/mo + {plan.usage_price_cents}c usage
                </p>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}
