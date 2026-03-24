"use client";

import DistributionBarChart from "@/components/charts/DistributionBarChart";
import MasteryPieChart from "@/components/charts/MasteryPieChart";
import ProgressLineChart from "@/components/charts/ProgressLineChart";
import PageHeader from "@/components/layouts/PageHeader";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useSuperAdminDashboard } from "@/hooks/useDashboard";

export default function SuperAdminDashboardPage() {
  const dashboard = useSuperAdminDashboard();

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Platform control"
        title="Track cross-tenant learning performance and platform health"
        description="This global dashboard combines real learner analytics, tenant distribution, and operational backlog signals for platform leadership."
      />

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Tenants" value={dashboard.kpis.totalTenants} tone="info" />
        <MetricCard title="Learners" value={dashboard.kpis.totalLearners} tone="success" />
        <MetricCard title="Avg completion" value={`${dashboard.kpis.averageCompletion}%`} tone="warning" />
        <MetricCard title="Avg mastery" value={`${dashboard.kpis.averageMastery}%`} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <ProgressLineChart
          title="Top tenant mastery"
          description="Average learner mastery across the largest tenants on the platform."
          data={dashboard.charts.tenantPerformanceLine}
        />
        <MasteryPieChart
          title="Global topic mastery"
          description="Cross-tenant mastery distribution aggregated from learner diagnostics."
          data={dashboard.charts.masteryPie}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <DistributionBarChart
          title="Role mix"
          description="Platform-wide distribution of learners and staff roles."
          data={dashboard.charts.roleMixBar}
        />
        <SurfaceCard title="Cross-tenant performance" description="Largest tenant cohorts ranked by learner volume and mastery.">
          <div className="space-y-3">
            {dashboard.tenantBreakdown.slice(0, 8).map((tenant) => (
              <div
                key={tenant.tenant_id}
                className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
              >
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{tenant.tenant_name}</p>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                  {tenant.student_count} learners • mastery {tenant.average_mastery_percent}% • completion {tenant.average_completion_percent}%
                </p>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SurfaceCard title="Tenant growth" description="Cumulative tenant creation based on the current tenant list.">
          <div className="space-y-3">
            {dashboard.charts.growthLine.map((point) => (
              <div
                key={point.label}
                className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-900/70"
              >
                <span className="font-medium text-slate-900 dark:text-slate-100">{point.label}</span>
                <span className="text-slate-600 dark:text-slate-400">Tenant #{point.progress}</span>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard title="Outbox watchlist" description="Dead-letter events and platform controls still stay visible next to analytics.">
          <div className="mb-4 grid gap-3 sm:grid-cols-3">
            <MetricCard title="Dead outbox" value={dashboard.kpis.deadOutbox} tone="warning" />
            <MetricCard title="Pending outbox" value={dashboard.kpis.pendingOutbox} tone="success" />
            <MetricCard title="Flags enabled" value={dashboard.kpis.enabledFlags} />
          </div>
          <div className="space-y-3">
            {dashboard.deadEvents.map((event) => (
              <div
                key={event.id}
                className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
              >
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{event.event_type}</p>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                  Attempts: {event.attempts} • Tenant {event.tenant_id ?? "platform"} • {event.status}
                </p>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}
