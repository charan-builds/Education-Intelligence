"use client";

import { AlertTriangle, Award, ShieldAlert, Users } from "lucide-react";

import ActivityFeed from "@/components/dashboard/ActivityFeed";
import RecommendationPanel from "@/components/dashboard/RecommendationPanel";
import DistributionBarChart from "@/components/charts/DistributionBarChart";
import ProgressLineChart from "@/components/charts/ProgressLineChart";
import PageHeader from "@/components/layouts/PageHeader";
import DataList from "@/components/ui/DataList";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useTeacherDashboard } from "@/hooks/useDashboard";

export default function TeacherDashboardPage() {
  const dashboard = useTeacherDashboard();

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Teacher workspace"
        title="Monitor learner momentum across the tenant"
        description="This dashboard surfaces cohort risk, weak-topic clusters, top performers, and intervention priorities from the new intelligence layer."
      />

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="story-card">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Cohort pulse</p>
          <p className="mt-3 text-2xl font-semibold text-slate-950 dark:text-slate-50">Teaching signals in one view</p>
          <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">Track risk, retention, and mastery without hunting through multiple screens.</p>
        </div>
        <div className="story-card">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Intervention lane</p>
          <p className="mt-3 text-2xl font-semibold text-slate-950 dark:text-slate-50">{dashboard.kpis.criticalCount} high-priority learners</p>
          <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">Critical risk and weak-retention signals stay visible so you can act earlier.</p>
        </div>
        <div className="story-card">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Retention watch</p>
          <p className="mt-3 text-2xl font-semibold text-slate-950 dark:text-slate-50">{dashboard.kpis.dueReviewCount} reviews due</p>
          <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">Spaced reinforcement pressure is highlighted before confidence drops across the cohort.</p>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Students" value={dashboard.kpis.studentCount} tone="info" icon={<Users className="h-5 w-5" />} />
        <MetricCard title="Critical risk" value={dashboard.kpis.criticalCount} tone="warning" icon={<ShieldAlert className="h-5 w-5" />} />
        <MetricCard title="Watchlist" value={dashboard.kpis.watchCount} tone="warning" icon={<AlertTriangle className="h-5 w-5" />} />
        <MetricCard title="Due reviews" value={dashboard.kpis.dueReviewCount} tone="success" icon={<Award className="h-5 w-5" />} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <ProgressLineChart
          title="Weak-topic cluster pressure"
          description="Topics with the largest class-wide mastery gaps."
          data={dashboard.charts.progressLine}
        />
        <DistributionBarChart
          title="Performance distribution"
          description="Current learner segmentation for intervention planning."
          data={dashboard.charts.clusteringBar}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <ProgressLineChart
          title="Retention trend"
          description="Average memory-retention signal over the last week."
          data={dashboard.charts.retentionLine}
        />
        <SurfaceCard
          title="Weak retention topics"
          description="Topics most likely to need spaced reinforcement."
          className="bg-[radial-gradient(circle_at_top_right,_rgba(250,204,21,0.14),_transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.99),rgba(248,250,252,0.96))] dark:bg-[radial-gradient(circle_at_top_right,_rgba(250,204,21,0.12),_transparent_34%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))]"
        >
          <DataList
            items={dashboard.retentionTopics}
            emptyTitle="Retention is stable"
            emptyDescription="No weak-retention topics are currently flagged for the class."
            getKey={(topic) => topic.topic_name}
            renderItem={(topic) => (
              <>
                <div className="flex items-center justify-between gap-4">
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{topic.topic_name}</p>
                  <p className="text-sm font-semibold text-amber-600 dark:text-amber-300">
                    {topic.average_retention_score}%
                  </p>
                </div>
              </>
            )}
          />
        </SurfaceCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <RecommendationPanel items={dashboard.recommendations} />
        <SurfaceCard
          title="Weak topic clusters"
          description="Lowest-scoring topics across the cohort."
          className="bg-[radial-gradient(circle_at_top_right,_rgba(244,63,94,0.12),_transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.99),rgba(248,250,252,0.96))] dark:bg-[radial-gradient(circle_at_top_right,_rgba(244,63,94,0.12),_transparent_34%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))]"
        >
          <DataList
            items={dashboard.charts.progressLine.slice(0, 6)}
            emptyTitle="No weak-topic clusters"
            emptyDescription="Cohort weak-topic pressure will appear here once new signals are available."
            getKey={(cluster) => cluster.label}
            renderItem={(cluster) => (
              <>
                <div className="flex items-center justify-between gap-4">
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{cluster.label}</p>
                  <p className="text-sm font-semibold text-amber-600 dark:text-amber-300">{cluster.progress}% gap</p>
                </div>
              </>
            )}
          />
        </SurfaceCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SurfaceCard
          title="Top students"
          description="Students with the strongest progress and score profile."
          className="bg-[radial-gradient(circle_at_top_right,_rgba(16,185,129,0.14),_transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.99),rgba(248,250,252,0.96))] dark:bg-[radial-gradient(circle_at_top_right,_rgba(16,185,129,0.12),_transparent_34%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))]"
        >
          <DataList
            items={dashboard.topStudents}
            emptyTitle="No standout learners yet"
            emptyDescription="Top performers will appear once learner progress has been recorded for this cohort."
            getKey={(learner) => String(learner.user_id)}
            renderItem={(learner) => (
              <>
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{learner.name}</p>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                      {learner.completion_percent}% completion • {learner.average_score}% avg score
                    </p>
                  </div>
                  <p className="text-sm font-semibold text-brand-700 dark:text-brand-200">{learner.xp} XP</p>
                </div>
              </>
            )}
          />
        </SurfaceCard>
        <ActivityFeed
          title="Instructional watchlist"
          description="Students who currently need the most attention."
          items={dashboard.riskStudents.map((learner) => ({
            title: learner.name,
            subtitle: `${learner.completion_percent}% completion • ${learner.average_score}% avg score`,
            tone: learner.risk_level === "critical" ? "danger" : "warning",
          }))}
        />
      </div>
    </div>
  );
}
