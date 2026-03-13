"use client";

export const dynamic = "force-dynamic";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";

import { startDiagnostic } from "@/services/diagnosticService";
import { getGoals } from "@/services/goalService";

export default function GoalSelectionPage() {
  const router = useRouter();
  const [selectedGoalId, setSelectedGoalId] = useState<number | null>(null);

  const goalsQuery = useQuery({
    queryKey: ["goals"],
    queryFn: getGoals,
  });

  const goals = useMemo(() => goalsQuery.data?.items ?? [], [goalsQuery.data?.items]);

  const startDiagnosticMutation = useMutation({
    mutationFn: async (goalId: number) => startDiagnostic(goalId),
    onSuccess: (session) => {
      router.push(`/diagnostic/test?test_id=${session.id}&goal_id=${session.goal_id}`);
    },
  });

  async function handleSubmit() {
    if (!selectedGoalId) {
      return;
    }
    await startDiagnosticMutation.mutateAsync(selectedGoalId);
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <h1 className="text-3xl font-semibold tracking-tight">Select Your Goal</h1>
      <p className="mt-2 text-slate-600">Choose your target path to start a personalized diagnostic test.</p>

      {goalsQuery.isLoading && <p className="mt-8 text-slate-600">Loading goals...</p>}
      {goalsQuery.isError && <p className="mt-8 text-red-600">Failed to load goals.</p>}

      {!goalsQuery.isLoading && !goalsQuery.isError && goals.length === 0 && (
        <p className="mt-8 text-slate-600">No goals available yet.</p>
      )}

      {goals.length > 0 && (
        <section className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {goals.map((goal) => {
            const selected = selectedGoalId === goal.id;
            return (
              <button
                key={goal.id}
                type="button"
                onClick={() => setSelectedGoalId(goal.id)}
                className={[
                  "rounded-xl border bg-white p-5 text-left shadow-sm transition",
                  selected
                    ? "border-brand-600 ring-2 ring-brand-200"
                    : "border-slate-200 hover:border-slate-300 hover:shadow",
                ].join(" ")}
              >
                <h2 className="text-lg font-semibold text-slate-900">{goal.name}</h2>
                <p className="mt-2 text-sm text-slate-600">{goal.description}</p>
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
          className="rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {startDiagnosticMutation.isPending ? "Starting..." : "Start Diagnostic"}
        </button>

        {startDiagnosticMutation.isError && (
          <p className="mt-3 text-sm text-red-600">Unable to start diagnostic for selected goal.</p>
        )}
      </div>
    </main>
  );
}
