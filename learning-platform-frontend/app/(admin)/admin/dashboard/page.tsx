"use client";
import { BookOpen, Flag, MessagesSquare, Target, Users } from "lucide-react";

import MasteryPieChart from "@/components/charts/MasteryPieChart";
import ProgressLineChart from "@/components/charts/ProgressLineChart";
import PageHeader from "@/components/layouts/PageHeader";
import MetricCard from "@/components/ui/MetricCard";
import QuickLinkCard from "@/components/ui/QuickLinkCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useAdminDashboard } from "@/hooks/useDashboard";

export default function AdminDashboardPage() {
  const dashboard = useAdminDashboard();

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Tenant admin"
        title="Run your tenant like a learning product"
        description="Users, topics, questions, goals, analytics, community moderation, and feature controls all roll up here from the FastAPI backend."
      />

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="story-card">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Operations</p>
          <p className="mt-3 text-2xl font-semibold text-slate-950 dark:text-slate-50">Content and people in one command view</p>
          <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">The admin workspace now separates content, learner, and feature-management signals more clearly.</p>
        </div>
        <div className="story-card">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Content graph</p>
          <p className="mt-3 text-2xl font-semibold text-slate-950 dark:text-slate-50">{dashboard.kpis.topics} topics</p>
          <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">Topics, questions, and goals are more visible now so the content system feels easier to manage.</p>
        </div>
        <div className="story-card">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Tenant controls</p>
          <p className="mt-3 text-2xl font-semibold text-slate-950 dark:text-slate-50">{dashboard.kpis.enabledFlags} active flags</p>
          <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">Feature availability and operational changes stay visible next to the core learning metrics.</p>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <MetricCard title="Users" value={dashboard.kpis.users} tone="info" icon={<Users className="h-5 w-5" />} />
        <MetricCard title="Topics" value={dashboard.kpis.topics} tone="success" icon={<BookOpen className="h-5 w-5" />} />
        <MetricCard title="Questions" value={dashboard.kpis.questions} tone="warning" />
        <MetricCard title="Goals" value={dashboard.kpis.goals} icon={<Target className="h-5 w-5" />} />
        <MetricCard title="Threads" value={dashboard.kpis.communityThreads} icon={<MessagesSquare className="h-5 w-5" />} />
        <MetricCard title="Flags on" value={dashboard.kpis.enabledFlags} icon={<Flag className="h-5 w-5" />} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <ProgressLineChart
          title="Learner completion"
          description="Completion levels for recent learners under this tenant."
          data={dashboard.charts.progressLine}
        />
        <MasteryPieChart
          title="Mastery distribution"
          description="Tenant-wide topic mastery from `/analytics/overview`."
          data={dashboard.charts.masteryPie}
        />
      </div>

      <SurfaceCard
        title="Control surfaces"
        description="Jump straight into the admin workflows you use most."
        className="bg-[radial-gradient(circle_at_top_right,_rgba(56,189,248,0.12),_transparent_34%),radial-gradient(circle_at_bottom_left,_rgba(16,185,129,0.1),_transparent_28%),linear-gradient(180deg,rgba(255,255,255,0.99),rgba(248,250,252,0.96))] dark:bg-[radial-gradient(circle_at_top_right,_rgba(56,189,248,0.1),_transparent_34%),radial-gradient(circle_at_bottom_left,_rgba(16,185,129,0.1),_transparent_28%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))]"
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[
            {
              href: "/admin/users",
              title: "User management",
              description: "Create and review tenant users.",
              icon: Users,
            },
            {
              href: "/admin/content",
              title: "Topic + question management",
              description: "Maintain content graph, practice questions, and imports.",
              icon: BookOpen,
            },
            {
              href: "/admin/goals",
              title: "Goal management",
              description: "Create learning goals and map them to topics.",
              icon: Target,
            },
            {
              href: "/admin/community",
              title: "Community moderation",
              description: "Track discussion health and resolve threads.",
              icon: MessagesSquare,
            },
            {
              href: "/admin/feature-flags",
              title: "Feature flags",
              description: "Turn tenant capabilities on or off.",
              icon: Flag,
            },
          ].map((item) => (
            <QuickLinkCard key={item.href} href={item.href} title={item.title} description={item.description} icon={item.icon} />
          ))}
        </div>
      </SurfaceCard>
    </div>
  );
}
