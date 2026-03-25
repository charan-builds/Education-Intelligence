"use client";

import { useQuery } from "@tanstack/react-query";

import ActivityFeed from "@/components/dashboard/ActivityFeed";
import RecommendationPanel from "@/components/dashboard/RecommendationPanel";
import DistributionBarChart from "@/components/charts/DistributionBarChart";
import MasteryPieChart from "@/components/charts/MasteryPieChart";
import PageHeader from "@/components/layouts/PageHeader";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useTeacherDashboard } from "@/hooks/useDashboard";
import { getLearningTrends, getWeakTopics } from "@/services/analyticsService";

export default function TeacherInsightsPage() {
  const dashboard = useTeacherDashboard();
  const weakTopicsQuery = useQuery({
    queryKey: ["analytics", "weak-topics"],
    queryFn: getWeakTopics,
  });
  const trendsQuery = useQuery({
    queryKey: ["analytics", "learning-trends"],
    queryFn: getLearningTrends,
  });

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
          description="Weak topics and learning trends that need instructor intervention."
          items={(weakTopicsQuery.data?.length
            ? weakTopicsQuery.data.map((topic) => ({
                title: topic.topic_name,
                subtitle: `${topic.mastery_score.toFixed(0)} mastery • confidence ${Math.round(topic.confidence_score * 100)}%`,
                tone: topic.mastery_score < 50 ? "warning" : "info",
              }))
            : dashboard.learners.slice(0, 6).map((learner) => ({
                title: learner.email,
                subtitle: `${learner.pending_steps} pending topics • ${learner.mastery_percent}% mastery`,
                tone: learner.pending_steps > 3 ? "warning" : "success",
              }))).slice(0, 6)}
        />
      </div>

      <SurfaceCard title="Learning trends" description="Daily event volume, time spent, completions, and retries for the tenant.">
        <div className="grid gap-4 md:grid-cols-4">
          {(trendsQuery.data?.slice(-4) ?? []).map((item) => (
            <div
              key={item.label}
              className="rounded-[28px] border border-slate-200 bg-white/75 p-5 dark:border-slate-700 dark:bg-slate-900/75"
            >
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{item.label}</p>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{item.events} events</p>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{item.minutes_spent.toFixed(1)} min</p>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{item.completions} completions</p>
            </div>
          ))}
          {!(trendsQuery.data?.length) ? (
            <p className="text-sm text-slate-500">Trend data will appear as learners generate more events.</p>
          ) : null}
        </div>
      </SurfaceCard>

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
