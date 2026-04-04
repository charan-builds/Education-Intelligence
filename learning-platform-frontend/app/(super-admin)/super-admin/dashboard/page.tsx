"use client";

import DistributionBarChart from "@/components/charts/DistributionBarChart";
import MasteryPieChart from "@/components/charts/MasteryPieChart";
import ProgressLineChart from "@/components/charts/ProgressLineChart";
import PageHeader from "@/components/layouts/PageHeader";
import DataList from "@/components/ui/DataList";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useSuperAdminDashboard } from "@/hooks/useDashboard";
import { describeTenantAudience, formatTenantTypeLabel } from "@/utils/tenantLabels";

export default function SuperAdminDashboardPage() {
  const dashboard = useSuperAdminDashboard();

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Platform control"
        title="Track cross-tenant learning performance and platform health"
        description="This global dashboard combines real learner analytics, tenant distribution, and operational backlog signals for platform leadership."
      />

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="story-card">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Platform view</p>
          <p className="mt-3 text-2xl font-semibold text-slate-950 dark:text-slate-50">A cleaner global snapshot</p>
          <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">Tenant mix, learner volume, and performance are now easier to scan without every widget using the same tone.</p>
        </div>
        <div className="story-card">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Institution footprint</p>
          <p className="mt-3 text-2xl font-semibold text-slate-950 dark:text-slate-50">{dashboard.kpis.institutionTenants} institutions</p>
          <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">Institution tenants and personal workspaces are visually separated more clearly in the leadership view.</p>
        </div>
        <div className="story-card">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Operational watch</p>
          <p className="mt-3 text-2xl font-semibold text-slate-950 dark:text-slate-50">{dashboard.kpis.deadOutbox} dead events</p>
          <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">Health and analytics now sit side by side so platform issues are visible next to growth signals.</p>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <MetricCard title="Tenants" value={dashboard.kpis.totalTenants} tone="info" />
        <MetricCard title="Learners" value={dashboard.kpis.totalLearners} tone="success" />
        <MetricCard title="Institutions" value={dashboard.kpis.institutionTenants} tone="info" />
        <MetricCard title="Personal workspaces" value={dashboard.kpis.personalWorkspaces} tone="warning" />
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
        <SurfaceCard
          title="Cross-tenant performance"
          description="Largest tenant cohorts ranked by learner volume and mastery."
          className="bg-[radial-gradient(circle_at_top_right,_rgba(56,189,248,0.12),_transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.99),rgba(248,250,252,0.96))] dark:bg-[radial-gradient(circle_at_top_right,_rgba(56,189,248,0.1),_transparent_34%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))]"
        >
          <DataList
            items={dashboard.tenantBreakdown.slice(0, 8)}
            emptyTitle="No tenant analytics yet"
            emptyDescription="Tenant-level performance snapshots will appear here once institutions begin sending learner signals."
            getKey={(tenant) => String(tenant.tenant_id)}
            renderItem={(tenant) => (
              <>
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{tenant.tenant_name}</p>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                  {formatTenantTypeLabel(tenant.tenant_type)} • {tenant.student_count} learners • mastery {tenant.average_mastery_percent}% • completion {tenant.average_completion_percent}%
                </p>
                <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                  {describeTenantAudience(tenant.tenant_type)}
                </p>
              </>
            )}
          />
        </SurfaceCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SurfaceCard
          title="Tenant growth"
          description="Cumulative tenant creation based on the current tenant list."
          className="bg-[radial-gradient(circle_at_top_right,_rgba(16,185,129,0.14),_transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.99),rgba(248,250,252,0.96))] dark:bg-[radial-gradient(circle_at_top_right,_rgba(16,185,129,0.12),_transparent_34%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))]"
        >
          <DataList
            items={dashboard.charts.growthLine}
            emptyTitle="No tenant growth events"
            emptyDescription="Growth milestones will appear once new institutions are onboarded."
            getKey={(point) => point.label}
            renderItem={(point) => (
              <div className="flex items-center justify-between gap-4 text-sm">
                <span className="font-medium text-slate-900 dark:text-slate-100">{point.label}</span>
                <span className="text-slate-600 dark:text-slate-400">Tenant #{point.progress}</span>
              </div>
            )}
          />
        </SurfaceCard>

        <SurfaceCard
          title="Outbox watchlist"
          description="Dead-letter events and platform controls still stay visible next to analytics."
          className="bg-[radial-gradient(circle_at_top_right,_rgba(245,158,11,0.14),_transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.99),rgba(248,250,252,0.96))] dark:bg-[radial-gradient(circle_at_top_right,_rgba(245,158,11,0.12),_transparent_34%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))]"
        >
          <div className="mb-4 grid gap-3 sm:grid-cols-3">
            <MetricCard title="Dead outbox" value={dashboard.kpis.deadOutbox} tone="warning" />
            <MetricCard title="Pending outbox" value={dashboard.kpis.pendingOutbox} tone="success" />
            <MetricCard title="Flags enabled" value={dashboard.kpis.enabledFlags} />
          </div>
          <DataList
            items={dashboard.deadEvents}
            emptyTitle="Outbox is healthy"
            emptyDescription="No dead-letter or pending watchlist items need super-admin attention right now."
            getKey={(event) => String(event.id)}
            renderItem={(event) => (
              <>
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{event.event_type}</p>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                  Attempts: {event.attempts} • Tenant {event.tenant_id ?? "platform"} • {event.status}
                </p>
              </>
            )}
          />
        </SurfaceCard>
      </div>
    </div>
  );
}
