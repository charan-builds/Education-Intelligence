"use client";

import Link from "next/link";
import { BookOpen, Flag, MessagesSquare, Target, Users } from "lucide-react";

import MasteryPieChart from "@/components/charts/MasteryPieChart";
import ProgressLineChart from "@/components/charts/ProgressLineChart";
import PageHeader from "@/components/layouts/PageHeader";
import MetricCard from "@/components/ui/MetricCard";
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

      <SurfaceCard title="Control surfaces" description="Jump straight into the admin workflows you use most.">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[
            {
              href: "/admin/users",
              title: "User management",
              description: "Create and review tenant users.",
            },
            {
              href: "/admin/content",
              title: "Topic + question management",
              description: "Maintain content graph, practice questions, and imports.",
            },
            {
              href: "/admin/goals",
              title: "Goal management",
              description: "Create learning goals and map them to topics.",
            },
            {
              href: "/admin/community",
              title: "Community moderation",
              description: "Track discussion health and resolve threads.",
            },
            {
              href: "/admin/feature-flags",
              title: "Feature flags",
              description: "Turn tenant capabilities on or off.",
            },
          ].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-[28px] border border-slate-200 bg-white/75 p-5 transition hover:-translate-y-1 hover:shadow-panel dark:border-slate-700 dark:bg-slate-900/75"
            >
              <p className="text-base font-semibold text-slate-950 dark:text-slate-100">{item.title}</p>
              <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-400">{item.description}</p>
            </Link>
          ))}
        </div>
      </SurfaceCard>
    </div>
  );
}
