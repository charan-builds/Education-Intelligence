"use client";

import ActivityFeed from "@/components/dashboard/ActivityFeed";
import RecommendationPanel from "@/components/dashboard/RecommendationPanel";
import DistributionBarChart from "@/components/charts/DistributionBarChart";
import MasteryPieChart from "@/components/charts/MasteryPieChart";
import PageHeader from "@/components/layouts/PageHeader";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useTeacherDashboard } from "@/hooks/useDashboard";

export default function TeacherInsightsPage() {
  const dashboard = useTeacherDashboard();

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Insights"
        title="Diagnostic and mastery insights"
        description="A closer view of weak-topic clustering, cohort status, and instructional recommendations."
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <MasteryPieChart
          title="Mastery distribution"
          description="Tenant-wide topic mastery levels from the analytics service."
          data={dashboard.charts.masteryPie}
        />
        <DistributionBarChart
          title="Intervention buckets"
          description="Students clustered by low, medium, and strong mastery bands."
          data={dashboard.charts.clusteringBar}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <RecommendationPanel items={dashboard.recommendations} />
        <ActivityFeed
          title="Batch analysis"
          description="Learners ordered by current completion pressure."
          items={dashboard.learners.slice(0, 6).map((learner) => ({
            title: learner.email,
            subtitle: `${learner.pending_steps} pending topics • ${learner.mastery_percent}% mastery`,
            tone: learner.pending_steps > 3 ? "warning" : "success",
          }))}
        />
      </div>

      <SurfaceCard title="Weak topic clustering" description="A simple operational summary that maps the current analytics buckets into action zones.">
        <div className="grid gap-4 md:grid-cols-3">
          {dashboard.charts.clusteringBar.map((item) => (
            <div
              key={item.label}
              className="rounded-[28px] border border-slate-200 bg-white/75 p-5 dark:border-slate-700 dark:bg-slate-900/75"
            >
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{item.label}</p>
              <p className="mt-3 text-3xl font-semibold text-slate-950 dark:text-slate-50">{item.value}</p>
            </div>
          ))}
        </div>
      </SurfaceCard>
    </div>
  );
}
