"use client";

import { Rocket, Sparkles } from "lucide-react";

import ActivityFeed from "@/components/dashboard/ActivityFeed";
import RecommendationPanel from "@/components/dashboard/RecommendationPanel";
import ProgressLineChart from "@/components/charts/ProgressLineChart";
import MasteryPieChart from "@/components/charts/MasteryPieChart";
import PageHeader from "@/components/layouts/PageHeader";
import ImmersiveQuestBoard from "@/components/student/ImmersiveQuestBoard";
import InteractiveChallengeLab from "@/components/student/InteractiveChallengeLab";
import ProgressStoryTimeline from "@/components/student/ProgressStoryTimeline";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import EmptyState from "@/components/ui/EmptyState";
import { normalizeRoadmapGenerationStatus, useStudentDashboard } from "@/hooks/useDashboard";

export default function StudentProgressPage() {
  const dashboard = useStudentDashboard();
  const topWeakTopic = dashboard.weakTopics[0];
  const level = Math.max(1, Math.floor(dashboard.kpis.xp / 250) + 1);
  const progressQuests = [
    {
      id: "progress-main",
      title: topWeakTopic ? `Master ${topWeakTopic.name}` : "Push the next chapter",
      description: "The platform translates analytics into a visible mission with a clear reward arc.",
      reward: "+150 XP",
      status: "active" as const,
    },
    {
      id: "progress-finish",
      title: "Close one more milestone",
      description: "A single completed step shifts the entire journey map and adds visual momentum.",
      reward: "Milestone celebration",
      status: dashboard.kpis.completed > 0 ? "completed" as const : "active" as const,
    },
    {
      id: "progress-unlock",
      title: "Unlock advanced chapter",
      description: "Sustain momentum to move from foundations to more specialized learning arcs.",
      reward: "Chapter unlock",
      status: dashboard.kpis.completionPercent >= 60 ? "completed" as const : "locked" as const,
    },
  ];
  const challengeSteps = dashboard.weakTopics.slice(0, 4).map((topic) => topic.name);
  const roadmapState = normalizeRoadmapGenerationStatus(dashboard.roadmap?.status);

  if (roadmapState !== "ready") {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Progress"
          title={roadmapState === "failed" ? "Progress is blocked" : "Progress unlocks after roadmap creation"}
          description={
            roadmapState === "failed"
              ? "The learner journey paused because roadmap generation failed."
              : "We are building the roadmap now so progress can reflect a real plan instead of an empty shell."
          }
        />
        <EmptyState
          title={roadmapState === "failed" ? "Roadmap failed to generate" : "Roadmap is still generating"}
          description={
            roadmapState === "failed"
              ? dashboard.roadmapErrorMessage ?? "Retry roadmap generation from the diagnostic result page."
              : "Return in a moment or open the roadmap page to watch the generation status."
          }
        />
      </div>
    );
  }

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

      <ImmersiveQuestBoard level={level} xp={dashboard.kpis.xp} streakDays={dashboard.kpis.streakDays} quests={progressQuests} />

      <ProgressStoryTimeline
        items={[
          {
            title: `Chapter 1: ${dashboard.kpis.completed} milestones conquered`,
            description: "Closed steps are presented like completed chapters so progress feels cumulative and memorable.",
            tone: "complete",
          },
          {
            title: `Chapter 2: ${dashboard.kpis.inProgress} active missions`,
            description: "Current work is framed as active quests rather than generic in-progress content.",
            tone: "active",
          },
          {
            title: topWeakTopic ? `Chapter 3: recover ${topWeakTopic.name}` : "Chapter 3 is ready to unlock",
            description: "The platform points to the next narrative beat that will produce the strongest visible improvement.",
            tone: "upcoming",
          },
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <ProgressLineChart
          title="Journey completion"
          description="An animated view of how each study push fills the broader adventure arc."
          data={dashboard.charts.progressLine}
        />
        <MasteryPieChart
          title="Chapter distribution"
          description="How the journey currently splits across conquered, active, and waiting stages."
          data={dashboard.charts.masteryPie}
        />
      </div>

      {challengeSteps.length >= 2 ? (
        <InteractiveChallengeLab chapterTitle="Weak-topic recovery sequence" chapterSteps={challengeSteps} />
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <ActivityFeed items={dashboard.recentActivity} />
        <RecommendationPanel items={dashboard.recommendations} />
      </div>
    </div>
  );
}
