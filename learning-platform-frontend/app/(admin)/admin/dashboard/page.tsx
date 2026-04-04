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
