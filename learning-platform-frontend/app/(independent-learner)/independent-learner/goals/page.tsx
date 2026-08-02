"use client";

export const dynamic = "force-dynamic";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, CheckCircle2, Clock3, Layers3, Sparkles, Target, TrendingUp } from "lucide-react";

import RequireRole from "@/components/auth/RequireRole";
import RoleDashboardLayout from "@/components/layout/RoleDashboardLayout";
import EmptyState from "@/components/ui/EmptyState";
import ErrorState from "@/components/ui/ErrorState";
import Skeleton from "@/components/ui/Skeleton";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { startDiagnostic } from "@/services/diagnosticService";
import { getCurrentGoal, getGoals, selectCurrentGoal } from "@/services/goalService";
import { appRoutes } from "@/utils/appRoutes";

function prettyDifficultyTag(value: string | null | undefined): string {
  if (!value) {
    return "Adaptive";
  }
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export default function IndependentLearnerGoalsPage() {
  const router = useRouter();
  const [selectedGoalId, setSelectedGoalId] = useState<number | null>(null);

  const goalsQuery = useQuery({
    queryKey: ["independent-learner", "goals"],
    queryFn: getGoals,
  });
  const currentGoalQuery = useQuery({
    queryKey: ["independent-learner", "goals", "current"],
    queryFn: getCurrentGoal,
  });

  const goals = useMemo(() => goalsQuery.data?.items ?? [], [goalsQuery.data?.items]);
  const selectedGoal = goals.find((goal) => goal.id === selectedGoalId) ?? null;

  useEffect(() => {
    if (selectedGoalId !== null) {
      return;
    }
    if (currentGoalQuery.data?.goal_id) {
      setSelectedGoalId(currentGoalQuery.data.goal_id);
      return;
    }
    const recommendedGoal = goals.find((goal) => goal.is_recommended);
    if (recommendedGoal) {
      setSelectedGoalId(recommendedGoal.id);
    }
  }, [currentGoalQuery.data?.goal_id, goals, selectedGoalId]);

  const continueMutation = useMutation({
    mutationFn: async (goalId: number) => {
      await selectCurrentGoal(goalId);
      return startDiagnostic(goalId);
    },
    onSuccess: (session) => {
      router.push(`${appRoutes.independentLearner.diagnostic}?test_id=${session.id}&goal_id=${session.goal_id}`);
    },
  });

  async function handleContinue() {
    if (!selectedGoalId) {
      return;
    }
    await continueMutation.mutateAsync(selectedGoalId);
  }

  return (
    <RequireRole allowedRoles={["independent_learner"]}>
      <RoleDashboardLayout
        roleLabel="Independent Learner"
        title="Choose Your Learning Goal"
        description="Select the destination that should drive your diagnostic difficulty, roadmap ordering, and recommendation bias."
        navItems={[
          { label: "Welcome", href: appRoutes.independentLearner.welcome },
          { label: "Onboarding", href: appRoutes.independentLearner.onboarding },
          { label: "Dashboard", href: appRoutes.independentLearner.dashboard },
        ]}
      >
        <div className="grid gap-6 xl:grid-cols-[1.08fr_0.92fr]">
          <SurfaceCard
            title="Goal cards"
            description="Each goal becomes the active destination for this workspace. Only one goal stays active at a time."
            className="border-violet-200 bg-[radial-gradient(circle_at_top_left,_rgba(168,85,247,0.16),_transparent_38%),linear-gradient(180deg,rgba(255,255,255,0.99),rgba(245,243,255,0.96))] dark:border-violet-700 dark:bg-[radial-gradient(circle_at_top_left,_rgba(168,85,247,0.16),_transparent_38%),linear-gradient(180deg,rgba(30,27,75,0.45),rgba(15,23,42,0.98))]"
          >
            {goalsQuery.isLoading ? (
              <div className="grid gap-4 md:grid-cols-2">
                {Array.from({ length: 4 }).map((_, index) => (
                  <Skeleton key={index} className="h-72" />
                ))}
              </div>
            ) : null}
            {goalsQuery.isError ? <ErrorState description="Failed to load goals." onRetry={() => void goalsQuery.refetch()} /> : null}
            {!goalsQuery.isLoading && !goalsQuery.isError && goals.length === 0 ? (
              <EmptyState title="No goals available yet" description="This workspace needs at least one published goal before diagnostics can begin." />
            ) : null}

            {goals.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2">
                {goals.map((goal) => {
                  const selected = selectedGoalId === goal.id;
                  return (
                    <button
                      key={goal.id}
                      type="button"
                      onClick={() => setSelectedGoalId(goal.id)}
                      className={[
                        "relative overflow-hidden rounded-[28px] border p-5 text-left transition duration-200",
                        selected
                          ? "border-violet-500 bg-gradient-to-br from-violet-50 via-fuchsia-50 to-white shadow-[0_26px_60px_-34px_rgba(139,92,246,0.5)] ring-2 ring-violet-100 dark:border-violet-400 dark:bg-violet-500/10 dark:ring-violet-500/10"
                          : "border-slate-200 bg-white/92 shadow-[0_18px_45px_-34px_rgba(15,23,42,0.25)] hover:-translate-y-0.5 hover:border-violet-200 hover:bg-white dark:border-slate-700 dark:bg-slate-950/72 dark:hover:border-violet-700",
                      ].join(" ")}
                    >
                      <div className="absolute right-0 top-0 h-24 w-24 rounded-full bg-violet-200/25 blur-2xl dark:bg-violet-500/10" />
                      <div className="relative">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div className="flex flex-wrap gap-2">
                            {goal.is_recommended ? (
                              <span className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:border-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-200">
                                <Sparkles className="h-3.5 w-3.5" />
                                Recommended
                              </span>
                            ) : null}
                            <span className="inline-flex items-center rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-700 dark:border-violet-700 dark:bg-violet-900/30 dark:text-violet-200">
                              {prettyDifficultyTag(goal.difficulty_tag)}
                            </span>
                          </div>
                          {selected ? <CheckCircle2 className="h-5 w-5 text-violet-600 dark:text-violet-300" /> : null}
                        </div>

                        <h2 className="mt-4 text-lg font-semibold text-slate-950 dark:text-slate-50">{goal.name}</h2>
                        <p className="mt-3 text-sm leading-7 text-slate-700 dark:text-slate-300">{goal.description}</p>

                        <div className="mt-4 grid gap-3 text-sm text-slate-700 dark:text-slate-300">
                          <div className="flex items-center gap-2">
                            <Clock3 className="h-4 w-4 text-violet-500" />
                            <span>{goal.estimated_duration_weeks ? `${goal.estimated_duration_weeks} week plan` : "Flexible duration"}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Layers3 className="h-4 w-4 text-violet-500" />
                            <span>{goal.skills_covered?.length ? goal.skills_covered.join(", ") : "Skills will adapt from your diagnostic"}</span>
                          </div>
                        </div>

                        <div className="mt-5 rounded-[22px] border border-violet-100 bg-white/90 p-4 text-sm leading-7 text-slate-700 dark:border-violet-800 dark:bg-slate-950/60 dark:text-slate-300">
                          <p className="font-semibold text-slate-950 dark:text-slate-100">Roadmap preview</p>
                          <p className="mt-2">{goal.roadmap_preview || "The platform will sequence fundamentals, weak concepts, and next best topics after your diagnostic completes."}</p>
                        </div>

                        <div className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-violet-700 dark:text-violet-300">
                          {selected ? "Selected goal" : "Click to select"}
                          <ArrowRight className="h-4 w-4" />
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            ) : null}
          </SurfaceCard>

          <SurfaceCard
            title="Selection summary"
            description="The active goal becomes the basis for your next diagnostic session and generated roadmap."
            className="border-violet-200 bg-violet-50/70 dark:border-violet-700 dark:bg-violet-900/20"
          >
            <div className="space-y-4">
              <div className="rounded-[26px] border border-violet-200 bg-white/90 p-5 dark:border-violet-700 dark:bg-slate-950/60">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-violet-500">Current active goal</p>
                <p className="mt-3 text-lg font-semibold text-slate-950 dark:text-slate-50">
                  {currentGoalQuery.data?.goal.name ?? "None selected yet"}
                </p>
                <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">
                  {currentGoalQuery.data?.goal.description ?? "Choose one goal to unlock the diagnostic and your personalized learning path."}
                </p>
              </div>

              <div className="rounded-[26px] border border-violet-200 bg-white/90 p-5 dark:border-violet-700 dark:bg-slate-950/60">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-violet-500">Selected for next step</p>
                <p className="mt-3 text-lg font-semibold text-slate-950 dark:text-slate-50">
                  {selectedGoal?.name ?? "Pick a goal card"}
                </p>
                <div className="mt-3 space-y-3 text-sm leading-7 text-slate-700 dark:text-slate-300">
                  <p>{selectedGoal?.roadmap_preview ?? "Once you choose a goal, the platform will immediately start a goal-aware diagnostic."}</p>
                  {selectedGoal?.is_recommended ? (
                    <p className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-700 dark:border-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-200">
                      <TrendingUp className="h-3.5 w-3.5" />
                      Recommended from your learner profile
                    </p>
                  ) : null}
                </div>
              </div>

              <div className="rounded-[26px] border border-violet-200 bg-white/90 p-5 dark:border-violet-700 dark:bg-slate-950/60">
                <div className="flex items-start gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white">
                    <Target className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-950 dark:text-slate-100">One active goal at a time</p>
                    <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">
                      Switching goals automatically deactivates the previous one so your diagnostic and roadmap always follow a single clear objective.
                    </p>
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={handleContinue}
                disabled={!selectedGoalId || continueMutation.isPending}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-violet-600 via-fuchsia-600 to-purple-500 px-5 py-3 text-sm font-semibold text-white shadow-[0_18px_45px_-22px_rgba(139,92,246,0.65)] transition hover:-translate-y-0.5 hover:from-violet-500 hover:via-fuchsia-500 hover:to-purple-400 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <ArrowRight className="h-4 w-4" />
                {continueMutation.isPending ? "Preparing diagnostic..." : "Continue"}
              </button>

              {continueMutation.isError ? (
                <p className="text-sm text-red-600">Unable to activate the selected goal and start the diagnostic.</p>
              ) : null}
            </div>
          </SurfaceCard>
        </div>
      </RoleDashboardLayout>
    </RequireRole>
  );
}
