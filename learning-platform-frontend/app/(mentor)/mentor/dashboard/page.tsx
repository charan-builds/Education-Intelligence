"use client";

import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Bot, BrainCircuit, MessagesSquare, Sparkles, ToggleLeft } from "lucide-react";

import ActivityFeed from "@/components/dashboard/ActivityFeed";
import RecommendationPanel from "@/components/dashboard/RecommendationPanel";
import MasteryPieChart from "@/components/charts/MasteryPieChart";
import ProgressLineChart from "@/components/charts/ProgressLineChart";
import PageHeader from "@/components/layouts/PageHeader";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import StatusPill from "@/components/ui/StatusPill";
import { normalizeRoadmapGenerationStatus, useMentorWorkspace } from "@/hooks/useDashboard";
import { runAutonomousAgent } from "@/services/mentorInsightsService";

export default function MentorDashboardPage() {
  const workspace = useMentorWorkspace();
  const queryClient = useQueryClient();
  const roadmapState = normalizeRoadmapGenerationStatus(workspace.roadmap?.status);

  const runAgentMutation = useMutation({
    mutationFn: runAutonomousAgent,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["dashboard", "mentor", "agent"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard", "mentor", "suggestions"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard", "mentor", "notifications"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard", "mentor", "roadmap", workspace.queries.roadmapQuery.data?.items?.[0]?.user_id] });
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Mentor workspace"
        title="Guide learners with live recommendation signals"
        description="The mentor panel surfaces current suggestions, weak-topic focus, notifications, and the visibility of the `ai_mentor_enabled` feature flag."
        actions={
          <Link
            href="/mentor/chat"
            className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-brand-700 via-brand-600 to-brand-500 px-4 py-3 text-sm font-semibold text-white shadow-glow"
          >
            Open mentor chat
            <MessagesSquare className="h-4 w-4" />
          </Link>
        }
        meta={
          <StatusPill
            label={workspace.kpis.aiMentorEnabled ? "AI mentor visibility on" : "AI mentor visibility off"}
            tone={workspace.kpis.aiMentorEnabled ? "success" : "warning"}
          />
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard title="AI visibility" value={workspace.kpis.aiMentorEnabled ? "Enabled" : "Disabled"} tone="info" icon={<ToggleLeft className="h-5 w-5" />} />
        <MetricCard title="Suggestions" value={workspace.kpis.recommendationCount} tone="success" icon={<Bot className="h-5 w-5" />} />
        <MetricCard title="Notifications" value={workspace.kpis.notificationCount} tone="warning" icon={<BrainCircuit className="h-5 w-5" />} />
        <MetricCard title="Agent decisions" value={workspace.kpis.agentDecisions} icon={<Sparkles className="h-5 w-5" />} />
      </div>

      {roadmapState !== "ready" ? (
        <EmptyState
          title={roadmapState === "failed" ? "Learner roadmap failed" : "Learner roadmap still generating"}
          description={
            roadmapState === "failed"
              ? workspace.roadmapErrorMessage ?? "Mentor guidance will become fully available after roadmap generation succeeds."
              : "Mentor guidance is waiting on the learner roadmap so recommendations stay grounded in the actual plan."
          }
        />
      ) : null}

      {roadmapState === "ready" ? (
        <>
          <SurfaceCard
            title="Autonomous agent"
            description="This agent continuously observes learner state, decides the next intervention, and explains each action in plain language."
            actions={
              <Button onClick={() => runAgentMutation.mutate()} disabled={runAgentMutation.isPending}>
                Run agent cycle
              </Button>
            }
          >
        <div className="grid gap-4 md:grid-cols-4">
          <MetricCard title="Risk level" value={workspace.agent?.observed_state.risk_level ?? "unknown"} tone="warning" />
          <MetricCard title="Focus score" value={Math.round(workspace.agent?.observed_state.focus_score ?? 0)} tone="default" />
          <MetricCard title="Streak" value={`${workspace.agent?.observed_state.streak_days ?? 0} days`} tone="success" />
          <MetricCard title="Next topic" value={workspace.agent?.observed_state.next_pending_topic?.topic_name ?? "None"} tone="info" />
        </div>
        <div className="mt-6 grid gap-6 xl:grid-cols-3">
          <div className="space-y-3">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Observed state</p>
            <div className="rounded-3xl border border-slate-200 bg-white/70 p-4 dark:border-slate-700 dark:bg-slate-900/70">
              <p className="text-sm leading-7 text-slate-700 dark:text-slate-300">
                {workspace.agent?.cycleSummary ?? "Agent state unavailable."}
              </p>
              <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">
                Learning style: {workspace.agent?.memorySummary.preferred_learning_style ?? "unknown"}.
              </p>
            </div>
          </div>
          <div className="space-y-3">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Decisions</p>
            {(workspace.agent?.decisions ?? []).map((item, index) => (
              <div key={`${item.title}-${index}`} className="rounded-3xl border border-indigo-200 bg-indigo-50/80 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-indigo-950">{item.title}</p>
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-700">
                    {Math.round(item.confidence * 100)}%
                  </span>
                </div>
                <p className="mt-2 text-sm leading-6 text-indigo-900/80">{item.why}</p>
              </div>
            ))}
          </div>
          <div className="space-y-3">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Actions</p>
            {(workspace.agent?.actions ?? []).map((item, index) => (
              <div key={`${item.title}-${index}`} className="rounded-3xl border border-emerald-200 bg-emerald-50/80 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-emerald-950">{item.title}</p>
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">
                    {item.status}
                  </span>
                </div>
                <p className="mt-2 text-sm leading-6 text-emerald-900/80">{item.why}</p>
              </div>
            ))}
          </div>
        </div>
          </SurfaceCard>

          <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <ProgressLineChart
              title="Weekly progress"
              description="Completion percentages returned by mentor progress analysis."
              data={workspace.charts.progressLine}
            />
            <MasteryPieChart
              title="Mentor focus mix"
              description="A mentor-friendly summary of pending support, focus topics, and completed roadmap work."
              data={workspace.charts.masteryPie}
            />
          </div>

          <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
            <RecommendationPanel items={workspace.suggestions.length > 0 ? workspace.suggestions : workspace.recommendedFocus} />
            <ActivityFeed
              title="Guidance alerts"
              description="Mentor notifications generated from roadmap and progress signals."
              items={workspace.notifications.map((item: { title: string; message: string; severity: string }) => ({
                title: item.title,
                subtitle: item.message,
                tone: item.severity,
              }))}
            />
          </div>

          <SurfaceCard title="Weak topic recommendations" description="Use these focus areas when coaching the learner through their next study block.">
            <div className="grid gap-3 md:grid-cols-2">
              {workspace.focusTopics.map((item) => (
                <div
                  key={item.topicId}
                  className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
                >
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Topic {item.topicId}</p>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">Improvement gap: {item.gap.toFixed(1)}</p>
                </div>
              ))}
            </div>
          </SurfaceCard>
        </>
      ) : null}
    </div>
  );
}
