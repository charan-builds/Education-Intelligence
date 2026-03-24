"use client";

import Link from "next/link";
import { Compass, Play, Sparkles } from "lucide-react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import PageHeader from "@/components/layouts/PageHeader";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorState from "@/components/ui/ErrorState";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useToast } from "@/components/providers/ToastProvider";
import { startDiagnostic } from "@/services/diagnosticService";
import { getGoals } from "@/services/goalService";

export default function StudentDiagnosticPage() {
  const router = useRouter();
  const { toast } = useToast();
  const goalsQuery = useQuery({
    queryKey: ["student", "diagnostic", "goals"],
    queryFn: getGoals,
  });

  const startMutation = useMutation({
    mutationFn: startDiagnostic,
    onSuccess: (session, goalId) => {
      toast({
        title: "Diagnostic started",
        description: `Opening adaptive diagnostic for goal ${goalId}.`,
        variant: "success",
      });
      router.push(`/diagnostic/test?goal_id=${goalId}&test_id=${session.id}`);
    },
    onError: () => {
      toast({
        title: "Diagnostic could not start",
        description: "The backend rejected the start request. Check your session and tenant context.",
        variant: "error",
      });
    },
  });

  const goals = goalsQuery.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Diagnostic"
        title="Launch an adaptive knowledge check"
        description="Choose a learning goal and start the diagnostic flow backed by `/diagnostic/start` and `/diagnostic/next-question`."
        meta={
          <>
            <MetricCard title="Available goals" value={goals.length} tone="info" />
            <MetricCard title="Adaptive engine" value="Active" tone="success" />
          </>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <SurfaceCard
          title="How it works"
          description="The backend creates a diagnostic session, serves adaptive questions, and scores the result for roadmap generation."
        >
          <div className="grid gap-3">
            {[
              "Select a goal aligned to your current learning target.",
              "Start the diagnostic session and answer adaptive questions.",
              "Use the result to generate a personalized roadmap.",
            ].map((step, index) => (
              <div
                key={step}
                className="flex gap-3 rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-100 text-brand-700 dark:bg-brand-900/50 dark:text-brand-100">
                  {index + 1}
                </div>
                <p className="text-sm leading-7 text-slate-700 dark:text-slate-300">{step}</p>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard title="Goal library" description="Start a diagnostic directly from any goal returned by the backend.">
          {goalsQuery.isLoading ? (
            <p className="text-sm text-slate-600 dark:text-slate-400">Loading goals...</p>
          ) : goalsQuery.isError ? (
            <ErrorState description="Goal loading failed. Verify the goals API is reachable." />
          ) : goals.length === 0 ? (
            <EmptyState
              title="No goals available"
              description="An admin needs to create at least one goal before a diagnostic can begin."
            />
          ) : (
            <div className="space-y-3">
              {goals.map((goal) => (
                <div
                  key={goal.id}
                  className="rounded-[28px] border border-slate-200 bg-white/75 p-5 dark:border-slate-700 dark:bg-slate-900/75"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-950 dark:text-slate-100">{goal.name}</p>
                      <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-400">{goal.description}</p>
                    </div>
                    <Button
                      onClick={() => startMutation.mutate(goal.id)}
                      disabled={startMutation.isPending}
                    >
                      <Play className="h-4 w-4" />
                      Start
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
          <div className="mt-5 flex flex-wrap gap-3">
            <Link href="/student/dashboard" className="inline-flex items-center gap-2 text-sm font-semibold text-brand-700 dark:text-brand-200">
              <Compass className="h-4 w-4" />
              Back to dashboard
            </Link>
            <Link href="/student/roadmap" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 dark:text-slate-300">
              <Sparkles className="h-4 w-4" />
              See roadmap area
            </Link>
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}
