"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { CheckCircle2, PlayCircle, Route, Sparkles, Wand2 } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import PageHeader from "@/components/layouts/PageHeader";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import StatusPill from "@/components/ui/StatusPill";
import { useToast } from "@/components/providers/ToastProvider";
import { useAuth } from "@/hooks/useAuth";
import { normalizeRoadmapGenerationStatus, normalizeRoadmapStatus, useStudentDashboard } from "@/hooks/useDashboard";
import { updateRoadmapStep } from "@/services/roadmapService";
import { getLearnerRoutes, getLearnerTopicPath } from "@/utils/appRoutes";

const ProgressLineChart = dynamic(() => import("@/components/charts/ProgressLineChart"));
const ImmersiveQuestBoard = dynamic(() => import("@/components/student/ImmersiveQuestBoard"));
const InteractiveChallengeLab = dynamic(() => import("@/components/student/InteractiveChallengeLab"));
const RoadmapFlow = dynamic(() => import("@/components/student/RoadmapFlow"));

export default function StudentRoadmapPage() {
  const { role } = useAuth();
  const learnerRoutes = getLearnerRoutes(role);
  const learnerLabel = role === "independent_learner" ? "Independent learner roadmap" : "Student roadmap";
  const dashboard = useStudentDashboard();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const updateStepMutation = useMutation({
    mutationFn: ({
      stepId,
      progressStatus,
    }: {
      stepId: number;
      progressStatus: "pending" | "in_progress" | "completed";
    }) => updateRoadmapStep(stepId, { progress_status: progressStatus }),
    onSuccess: async () => {
      toast({
        title: "Roadmap updated",
        description: "Your step progress has been synced with the backend.",
        variant: "success",
      });
      await queryClient.invalidateQueries({ queryKey: ["dashboard", "student", "roadmap"] });
    },
  });

  const level = Math.max(1, Math.floor(dashboard.kpis.xp / 250) + 1);
  const activeQuestTopic = dashboard.weakTopics[0]?.name ?? dashboard.topicMap.get(dashboard.steps[0]?.topic_id ?? 0) ?? "Foundations";
  const quests = [
    {
      id: "quest-current",
      title: `Recover ${activeQuestTopic}`,
      description: "Resolve the highest-leverage concept gap to unlock cleaner downstream progress.",
      reward: "+120 XP and momentum boost",
      status: "active" as const,
    },
    {
      id: "quest-streak",
      title: "Keep the streak shield alive",
      description: `Stay active for ${Math.max(3, dashboard.kpis.streakDays + 1)} days to stabilize your learning rhythm.`,
      reward: "Streak badge",
      status: dashboard.kpis.streakDays >= 3 ? "completed" as const : "active" as const,
    },
    {
      id: "quest-chapter",
      title: "Unlock the next chapter",
      description: "Complete the active mission chain to move into the next progression band.",
      reward: "Chapter unlock",
      status: dashboard.kpis.inProgress > 0 ? "active" as const : "locked" as const,
    },
  ];
  const challengeSteps = dashboard.steps
    .slice(0, 4)
    .map((step) => dashboard.topicMap.get(step.topic_id) ?? `Topic ${step.topic_id}`);
  const roadmapState = normalizeRoadmapGenerationStatus(dashboard.roadmap?.status);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={learnerLabel}
        title="Navigate your personalized learning sequence"
        description={
          role === "independent_learner"
            ? "Your personal workspace turns the roadmap into a visual journey with AI guidance, knowledge-graph context, and step-by-step progression."
            : "This workspace turns the roadmap into a visual journey with AI-powered next actions, graph storytelling, and step-by-step progression."
        }
        actions={
          <Link
            href={learnerRoutes.mentor}
            className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 text-sm font-semibold text-slate-900 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          >
            Mentor guidance
            <Sparkles className="h-4 w-4" />
          </Link>
        }
      />

      {roadmapState !== "ready" ? (
        <EmptyState
          title={roadmapState === "failed" ? "Roadmap generation failed" : "Roadmap is being prepared"}
          description={
            roadmapState === "failed"
              ? dashboard.roadmapErrorMessage ?? "We could not build your roadmap from the latest diagnostic yet. Your last synchronized progress remains available elsewhere in the workspace."
              : "Your diagnostic is complete and the roadmap is still generating. This page will become available as soon as it is ready."
          }
        />
      ) : dashboard.steps.length === 0 ? (
        <EmptyState
          title="No roadmap available"
          description="Complete a diagnostic and generate a roadmap before tracking topics here."
        />
      ) : (
        <>
          <motion.section
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="premium-hero soft-ring relative overflow-hidden rounded-[34px] border border-white/80 p-6 shadow-[0_28px_75px_-36px_rgba(15,23,42,0.22)]"
          >
            <div className="premium-orb left-0 top-0 h-24 w-24 bg-teal-300/25" />
            <div className="premium-orb right-0 top-10 h-28 w-28 bg-orange-300/25" style={{ animationDelay: "1.1s" }} />
            <div className="relative grid gap-4 lg:grid-cols-3">
              <div className="story-card">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Unlock path</p>
                <p className="mt-3 text-2xl font-semibold text-slate-950">{dashboard.kpis.totalSteps} mapped steps</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">A structured sequence instead of a flat content catalog.</p>
              </div>
              <div className="story-card">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Now advancing</p>
                <p className="mt-3 text-2xl font-semibold text-slate-950">{dashboard.kpis.inProgress} active missions</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">Each active step keeps the user inside a visible progression loop.</p>
              </div>
              <div className="story-card">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">AI assist</p>
                <p className="mt-3 text-2xl font-semibold text-slate-950">Explain or quiz any step</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">Every roadmap node can hand off directly to the mentor for support.</p>
              </div>
            </div>
          </motion.section>

          <div className="grid gap-4 md:grid-cols-3">
            <MetricCard title="Total steps" value={dashboard.kpis.totalSteps} tone="info" icon={<Route className="h-5 w-5" />} />
            <MetricCard title="Completed" value={dashboard.kpis.completed} tone="success" icon={<CheckCircle2 className="h-5 w-5" />} />
            <MetricCard title="In progress" value={dashboard.kpis.inProgress} tone="warning" icon={<PlayCircle className="h-5 w-5" />} />
          </div>

          <ImmersiveQuestBoard level={level} xp={dashboard.kpis.xp} streakDays={dashboard.kpis.streakDays} quests={quests} />

          <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <RoadmapFlow
              steps={dashboard.steps}
              topics={Array.from(dashboard.topicMap.entries()).map(([id, name]) => ({ id, name }))}
              weakTopicIds={dashboard.weakTopics.map((item) => item.topicId)}
            />
            <ProgressLineChart
              title="Completion trend"
              description="Step-by-step completion progression across the generated roadmap."
              data={dashboard.charts.progressLine}
            />
          </div>

          {challengeSteps.length >= 2 ? (
            <InteractiveChallengeLab chapterTitle="Chapter sequencing" chapterSteps={challengeSteps} />
          ) : null}

          <SurfaceCard
            title="Mission planner"
            description="Update individual roadmap missions, claim progress, and jump into topic learning pages."
            className="bg-[radial-gradient(circle_at_top_right,_rgba(14,165,233,0.12),_transparent_36%),linear-gradient(180deg,rgba(255,255,255,0.99),rgba(248,250,252,0.96))] dark:bg-[radial-gradient(circle_at_top_right,_rgba(14,165,233,0.1),_transparent_36%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))]"
          >
            <div className="space-y-3">
              {dashboard.steps.map((step) => {
                const status = normalizeRoadmapStatus(step.progress_status);
                return (
                  <div
                    key={step.id}
                    className="rounded-[28px] border border-slate-200 bg-white/92 p-5 shadow-[0_18px_45px_-34px_rgba(15,23,42,0.24)] transition hover:-translate-y-0.5 hover:border-slate-300 dark:border-slate-700 dark:bg-slate-950/76 dark:hover:border-slate-500"
                  >
                    <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                      <div>
                        <div className="flex flex-wrap items-center gap-3">
                          <p className="text-base font-semibold text-slate-950 dark:text-slate-100">
                            {dashboard.topicMap.get(step.topic_id) ?? `Topic ${step.topic_id}`}
                          </p>
                          <StatusPill
                            label={status}
                            tone={status === "completed" ? "success" : status === "in_progress" ? "warning" : "default"}
                          />
                        </div>
                        <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-400">
                          Quest {step.priority} • {step.phase ?? "Learning phase"} • {step.estimated_time_hours}h • {step.difficulty}
                        </p>
                        <p className="mt-2 text-xs uppercase tracking-[0.2em] text-slate-400">
                          {status === "completed"
                            ? "Achievement captured"
                            : status === "in_progress"
                              ? "Mission underway"
                              : "Ready to launch"}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Link
                          href={getLearnerTopicPath(role, step.topic_id)}
                          className="inline-flex items-center justify-center rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-900 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
                        >
                          Open topic
                        </Link>
                        <Link
                          href={`${learnerRoutes.mentor}?prompt=${encodeURIComponent(
                            `Explain ${
                              dashboard.topicMap.get(step.topic_id) ?? `Topic ${step.topic_id}`
                            } clearly, tell me why it matters in the roadmap, and give me one quick example.`,
                          )}`}
                          className="inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-900 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
                        >
                          Explain
                          <Sparkles className="h-4 w-4" />
                        </Link>
                        <Link
                          href={`${learnerRoutes.mentor}?prompt=${encodeURIComponent(
                            `Generate 3 practice questions for ${
                              dashboard.topicMap.get(step.topic_id) ?? `Topic ${step.topic_id}`
                            } with concise answers.`,
                          )}`}
                          className="inline-flex items-center justify-center gap-2 rounded-2xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white"
                        >
                          Quiz me
                          <Wand2 className="h-4 w-4 text-amber-300" />
                        </Link>
                        {status === "pending" ? (
                          <Button
                            onClick={() => updateStepMutation.mutate({ stepId: step.id, progressStatus: "in_progress" })}
                            disabled={updateStepMutation.isPending}
                          >
                            Start
                          </Button>
                        ) : null}
                        {status !== "completed" ? (
                          <Button
                            onClick={() => updateStepMutation.mutate({ stepId: step.id, progressStatus: "completed" })}
                            disabled={updateStepMutation.isPending}
                            variant="secondary"
                          >
                            Complete
                          </Button>
                        ) : (
                          <Button
                            onClick={() => updateStepMutation.mutate({ stepId: step.id, progressStatus: "in_progress" })}
                            disabled={updateStepMutation.isPending}
                            variant="ghost"
                          >
                            Reopen
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </SurfaceCard>
        </>
      )}
    </div>
  );
}
