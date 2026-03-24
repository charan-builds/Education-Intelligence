"use client";

import { Rocket, Sparkles } from "lucide-react";

import ActivityFeed from "@/components/dashboard/ActivityFeed";
import RecommendationPanel from "@/components/dashboard/RecommendationPanel";
import ProgressLineChart from "@/components/charts/ProgressLineChart";
import MasteryPieChart from "@/components/charts/MasteryPieChart";
import PageHeader from "@/components/layouts/PageHeader";
import ProgressStoryTimeline from "@/components/student/ProgressStoryTimeline";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useStudentDashboard } from "@/hooks/useDashboard";

export default function StudentProgressPage() {
  const dashboard = useStudentDashboard();
  const topWeakTopic = dashboard.weakTopics[0];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Progress"
        title="Understand your momentum"
        description="Track how learning effort turns into mastery, where your biggest lift is happening, and what the next turning point looks like."
      />

      <SurfaceCard
        title="Momentum narrative"
        description="A story-first summary for demo conversations, investor screenshares, and learner motivation."
        className="premium-hero"
        actions={
          <div className="inline-flex items-center gap-2 rounded-full bg-slate-950 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-white">
            <Rocket className="h-3.5 w-3.5 text-amber-300" />
            Momentum engine
          </div>
        }
      >
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="story-card">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Trend</p>
            <p className="mt-3 text-2xl font-semibold text-slate-950">{dashboard.kpis.completionPercent}% complete</p>
            <p className="mt-2 text-sm leading-6 text-slate-600">The learner is visibly progressing instead of staring at a static dashboard.</p>
          </div>
          <div className="story-card">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Focus zone</p>
            <p className="mt-3 text-2xl font-semibold text-slate-950">{topWeakTopic?.name ?? "High-confidence review"}</p>
            <p className="mt-2 text-sm leading-6 text-slate-600">Weak-topic pressure is translated into an actionable storyline.</p>
          </div>
          <div className="story-card">
            <div className="flex items-center gap-2 text-brand-700">
              <Sparkles className="h-4 w-4" />
              <p className="text-xs font-semibold uppercase tracking-[0.24em]">Coach signal</p>
            </div>
            <p className="mt-3 text-2xl font-semibold text-slate-950">{dashboard.mentorSuggestions.length} AI nudges</p>
            <p className="mt-2 text-sm leading-6 text-slate-600">Mentor intelligence turns analytics into the next best move.</p>
          </div>
        </div>
      </SurfaceCard>

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Completion" value={`${dashboard.kpis.completionPercent}%`} tone="info" />
        <MetricCard title="Completed steps" value={dashboard.kpis.completed} tone="success" />
        <MetricCard title="Active steps" value={dashboard.kpis.inProgress} tone="warning" />
        <MetricCard title="Weak topics" value={dashboard.kpis.weakTopicCount} />
      </div>

      <ProgressStoryTimeline
        items={[
          {
            title: `${dashboard.kpis.completed} steps completed`,
            description: "Closed steps create the feeling of real advancement and visible learning velocity.",
            tone: "complete",
          },
          {
            title: `${dashboard.kpis.inProgress} active focus areas`,
            description: "Current work is framed as active missions rather than generic in-progress content.",
            tone: "active",
          },
          {
            title: topWeakTopic ? `${topWeakTopic.name} is the next inflection point` : "The next inflection point is ready",
            description: "The platform can point to a specific concept that will most improve confidence and progress.",
            tone: "upcoming",
          },
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <ProgressLineChart
          title="Roadmap completion"
          description="A stepwise view of completion as you move through the roadmap."
          data={dashboard.charts.progressLine}
        />
        <MasteryPieChart
          title="Status distribution"
          description="How your roadmap currently splits across completed, active, and pending work."
          data={dashboard.charts.masteryPie}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <ActivityFeed items={dashboard.recentActivity} />
        <RecommendationPanel items={dashboard.recommendations} />
      </div>
    </div>
  );
}
