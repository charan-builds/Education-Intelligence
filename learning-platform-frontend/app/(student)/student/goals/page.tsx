"use client";

export const dynamic = "force-dynamic";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, CheckCircle2, Radar, Sparkles, Target } from "lucide-react";

import RequireRole from "@/components/auth/RequireRole";
import RoleDashboardLayout from "@/components/layout/RoleDashboardLayout";
import EmptyState from "@/components/ui/EmptyState";
import ErrorState from "@/components/ui/ErrorState";
import Skeleton from "@/components/ui/Skeleton";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { startDiagnostic } from "@/services/diagnosticService";
import { getGoals } from "@/services/goalService";
import { useAuth } from "@/hooks/useAuth";
import { getLearnerRoutes } from "@/utils/appRoutes";

export default function StudentGoalsPage() {
  const router = useRouter();
  const { role } = useAuth();
  const learnerRoutes = getLearnerRoutes(role);
  const [selectedGoalId, setSelectedGoalId] = useState<number | null>(null);

  const goalsQuery = useQuery({
    queryKey: ["goals"],
    queryFn: getGoals,
  });

  const goals = useMemo(() => goalsQuery.data?.items ?? [], [goalsQuery.data?.items]);

  const startDiagnosticMutation = useMutation({
    mutationFn: async (goalId: number) => startDiagnostic(goalId),
    onSuccess: (session) => {
      router.push(`${learnerRoutes.diagnostic}?test_id=${session.id}&goal_id=${session.goal_id}`);
    },
  });

  async function handleSubmit() {
    if (!selectedGoalId) {
      return;
    }
    await startDiagnosticMutation.mutateAsync(selectedGoalId);
  }

  return (
    <RequireRole allowedRoles={["student", "independent_learner", "teacher", "admin", "super_admin"]}>
      <RoleDashboardLayout
        roleLabel="Learning Flow"
        title="Select Your Goal"
        description="Choose the target path that should drive diagnostic question selection and roadmap generation."
        navItems={[
          { label: "Learning Dashboard", href: learnerRoutes.dashboard },
          { label: "Diagnostic", href: learnerRoutes.diagnostic },
          { label: "Roadmap", href: learnerRoutes.roadmap },
        ]}
      >
        <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
          <SurfaceCard
            title="How goal selection works"
            description="Pick the learning destination that should shape your diagnostic, recommendations, and roadmap."
            className="bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.14),_transparent_36%),linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.96))] dark:bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.12),_transparent_36%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))]"
          >
            <div className="grid gap-4">
              {[
                {
                  icon: <Target className="h-5 w-5" />,
                  title: "Choose the right destination",
                  body: "Each goal changes which topics the platform prioritizes and how the adaptive diagnostic responds to your answers.",
                },
                {
                  icon: <Radar className="h-5 w-5" />,
                  title: "Run an adaptive diagnostic",
                  body: "The system uses your selected goal to decide which questions to ask next and where the biggest skill gaps are.",
                },
                {
                  icon: <Sparkles className="h-5 w-5" />,
                  title: "Get a clearer roadmap",
                  body: "Once the diagnostic finishes, your roadmap, recommendations, and mentor guidance all follow this goal context.",
                },
              ].map((step, index) => (
                <div
                  key={step.title}
                  className="rounded-[26px] border border-slate-200 bg-white/88 p-5 shadow-[0_16px_40px_-30px_rgba(15,23,42,0.25)] dark:border-slate-700 dark:bg-slate-950/72"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 to-cyan-500 text-white shadow-[0_14px_30px_-18px_rgba(14,165,233,0.8)]">
                      {step.icon}
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">Step {index + 1}</p>
                      <h2 className="mt-2 text-base font-semibold text-slate-950 dark:text-slate-50">{step.title}</h2>
                      <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">{step.body}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </SurfaceCard>

          <SurfaceCard
            title="Available Goals"
            description="These goals are loaded from the backend `/goals` API. Select one to begin the learner flow."
            className="bg-[radial-gradient(circle_at_top_right,_rgba(16,185,129,0.14),_transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.99),rgba(248,250,252,0.97))] dark:bg-[radial-gradient(circle_at_top_right,_rgba(16,185,129,0.12),_transparent_34%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))]"
          >
          {goalsQuery.isLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} className="h-40" />
              ))}
            </div>
          ) : null}
          {goalsQuery.isError ? <ErrorState description="Failed to load goals." onRetry={() => void goalsQuery.refetch()} /> : null}
          {!goalsQuery.isLoading && !goalsQuery.isError && goals.length === 0 ? (
            <EmptyState title="No goals available yet" description="An admin needs to publish at least one goal before a learner can begin." />
          ) : null}

          {goals.length > 0 && (
            <section className="grid gap-4 md:grid-cols-2">
              {goals.map((goal) => {
                const selected = selectedGoalId === goal.id;
                return (
                  <button
                    key={goal.id}
                    type="button"
                    onClick={() => setSelectedGoalId(goal.id)}
                    className={[
                      "group relative overflow-hidden rounded-[28px] border p-5 text-left transition duration-200",
                      selected
                        ? "border-sky-500 bg-gradient-to-br from-sky-50 via-cyan-50 to-white shadow-[0_26px_60px_-34px_rgba(14,165,233,0.55)] ring-2 ring-sky-100 dark:border-sky-400 dark:bg-sky-500/10 dark:ring-sky-500/10"
                        : "border-slate-200 bg-white/92 shadow-[0_18px_45px_-34px_rgba(15,23,42,0.25)] hover:-translate-y-0.5 hover:border-slate-300 hover:bg-white dark:border-slate-700 dark:bg-slate-950/72 dark:hover:border-slate-500 dark:hover:bg-slate-950",
                    ].join(" ")}
                  >
                    <div className="absolute right-0 top-0 h-24 w-24 rounded-full bg-sky-200/25 blur-2xl transition group-hover:bg-sky-300/35 dark:bg-sky-500/10" />
                    <div className="relative">
                      <div className="flex items-start justify-between gap-3">
                        <div className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
                          Goal #{goal.id}
                        </div>
                        {selected ? <CheckCircle2 className="h-5 w-5 text-sky-600 dark:text-sky-300" /> : null}
                      </div>
                      <h2 className="mt-4 text-lg font-semibold text-slate-950 dark:text-slate-50">{goal.name}</h2>
                      <p className="mt-3 text-sm leading-7 text-slate-700 dark:text-slate-300">{goal.description}</p>
                      <div className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-sky-700 dark:text-sky-300">
                        {selected ? "Selected for diagnostic" : "Click to select this goal"}
                        <ArrowRight className="h-4 w-4" />
                      </div>
                    </div>
                  </button>
                );
              })}
            </section>
          )}

          <div className="mt-8 flex flex-col gap-4 rounded-[28px] border border-slate-200 bg-white/90 p-5 shadow-[0_18px_45px_-34px_rgba(15,23,42,0.24)] dark:border-slate-700 dark:bg-slate-950/70">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Current selection</p>
              <p className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">
                {selectedGoalId ? goals.find((goal) => goal.id === selectedGoalId)?.name ?? `Goal #${selectedGoalId}` : "No goal selected yet"}
              </p>
              <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">
                {selectedGoalId
                  ? "Start the adaptive diagnostic and the platform will begin tailoring your roadmap to this goal."
                  : "Choose a goal card above to unlock the diagnostic start action."}
              </p>
            </div>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!selectedGoalId || startDiagnosticMutation.isPending}
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-sky-600 via-cyan-600 to-emerald-500 px-5 py-3 text-sm font-semibold text-white shadow-[0_18px_45px_-22px_rgba(14,165,233,0.65)] transition hover:-translate-y-0.5 hover:from-sky-500 hover:via-cyan-500 hover:to-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Radar className="h-4 w-4" />
              {startDiagnosticMutation.isPending ? "Starting..." : "Start Diagnostic"}
            </button>

            {startDiagnosticMutation.isError ? (
              <p className="mt-3 text-sm text-red-600">Unable to start diagnostic for the selected goal.</p>
            ) : null}
          </div>
          </SurfaceCard>
        </div>
      </RoleDashboardLayout>
    </RequireRole>
  );
}
