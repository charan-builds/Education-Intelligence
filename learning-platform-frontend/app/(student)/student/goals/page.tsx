"use client";

export const dynamic = "force-dynamic";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";

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
        <SurfaceCard title="Available Goals" description="These goals are loaded from the backend `/goals` API.">
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
            <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {goals.map((goal) => {
                const selected = selectedGoalId === goal.id;
                return (
                  <button
                    key={goal.id}
                    type="button"
                    onClick={() => setSelectedGoalId(goal.id)}
                    className={[
                      "rounded-[24px] border bg-white p-5 text-left shadow-sm transition",
                      selected
                        ? "border-sky-500 ring-2 ring-sky-100"
                        : "border-slate-200 hover:border-slate-300 hover:shadow",
                    ].join(" ")}
                  >
                    <h2 className="text-lg font-semibold text-slate-900">{goal.name}</h2>
                    <p className="mt-2 text-sm leading-7 text-slate-600">{goal.description}</p>
                  </button>
                );
              })}
            </section>
          )}

          <div className="mt-8">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!selectedGoalId || startDiagnosticMutation.isPending}
              className="rounded-xl bg-sky-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {startDiagnosticMutation.isPending ? "Starting..." : "Start Diagnostic"}
            </button>

            {startDiagnosticMutation.isError ? (
              <p className="mt-3 text-sm text-red-600">Unable to start diagnostic for the selected goal.</p>
            ) : null}
          </div>
        </SurfaceCard>
      </RoleDashboardLayout>
    </RequireRole>
  );
}
