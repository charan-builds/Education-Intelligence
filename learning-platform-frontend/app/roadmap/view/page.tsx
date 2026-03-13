"use client";

export const dynamic = "force-dynamic";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { useAuth } from "@/hooks/useAuth";
import { getUserRoadmap } from "@/services/roadmapService";
import type { RoadmapStep } from "@/types/roadmap";

function normalizeStatus(status: string): "completed" | "in_progress" | "pending" {
  const value = status.toLowerCase();
  if (value === "completed") {
    return "completed";
  }
  if (value === "in_progress") {
    return "in_progress";
  }
  return "pending";
}

type PhaseGroup = {
  phaseTitle: string;
  steps: RoadmapStep[];
};

function groupStepsByPhase(steps: RoadmapStep[]): PhaseGroup[] {
  if (steps.length === 0) {
    return [
      { phaseTitle: "Phase 1 - Foundations", steps: [] },
      { phaseTitle: "Phase 2 - Intermediate Skills", steps: [] },
      { phaseTitle: "Phase 3 - Advanced Specialization", steps: [] },
    ];
  }

  const ordered = [...steps].sort((a, b) => a.priority - b.priority);
  const chunkSize = Math.ceil(ordered.length / 3);

  return [
    { phaseTitle: "Phase 1 - Foundations", steps: ordered.slice(0, chunkSize) },
    { phaseTitle: "Phase 2 - Intermediate Skills", steps: ordered.slice(chunkSize, chunkSize * 2) },
    { phaseTitle: "Phase 3 - Advanced Specialization", steps: ordered.slice(chunkSize * 2) },
  ];
}

export default function RoadmapViewPage() {
  const { user, isAuthenticated } = useAuth();

  const roadmapQuery = useQuery({
    queryKey: ["roadmap-view", user?.user_id],
    queryFn: async () => {
      if (!user?.user_id) {
        throw new Error("Missing user id");
      }
      return getUserRoadmap(user.user_id);
    },
    enabled: Boolean(isAuthenticated && user?.user_id),
  });

  const roadmap = roadmapQuery.data?.items?.[0] ?? null;

  const orderedSteps = useMemo(
    () => [...(roadmap?.steps ?? [])].sort((a, b) => a.priority - b.priority),
    [roadmap?.steps],
  );

  const progress = useMemo(() => {
    const total = orderedSteps.length;
    const completed = orderedSteps.filter((step) => normalizeStatus(step.progress_status) === "completed").length;
    const inProgress = orderedSteps.filter((step) => normalizeStatus(step.progress_status) === "in_progress").length;
    const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
    return { total, completed, inProgress, percent };
  }, [orderedSteps]);

  const phaseGroups = useMemo(() => groupStepsByPhase(orderedSteps), [orderedSteps]);

  if (!isAuthenticated) {
    return (
      <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
        <h1 className="text-3xl font-semibold tracking-tight">Roadmap View</h1>
        <p className="mt-3 text-slate-600">Please login to view your roadmap.</p>
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <h1 className="text-3xl font-semibold tracking-tight">Roadmap</h1>
      <p className="mt-2 text-slate-600">Roadmap steps grouped by phase.</p>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-slate-500">Completion Progress</p>
            <p className="text-3xl font-semibold text-slate-900">{progress.percent}%</p>
            <p className="text-sm text-slate-600">
              {progress.completed}/{progress.total} completed • {progress.inProgress} in progress
            </p>
          </div>
          <div className="w-full max-w-md">
            <div className="h-3 w-full rounded-full bg-slate-200">
              <div className="h-3 rounded-full bg-brand-600 transition-all" style={{ width: `${progress.percent}%` }} />
            </div>
          </div>
        </div>
      </section>

      {roadmapQuery.isLoading && <p className="mt-6 text-slate-600">Loading roadmap...</p>}
      {roadmapQuery.isError && <p className="mt-6 text-red-600">Failed to fetch roadmap.</p>}

      {!roadmapQuery.isLoading && !roadmapQuery.isError && orderedSteps.length === 0 && (
        <p className="mt-6 text-slate-600">No roadmap found for this user.</p>
      )}

      <section className="mt-6 space-y-6">
        {phaseGroups.map((phase) => (
          <article key={phase.phaseTitle} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">{phase.phaseTitle}</h2>

            {phase.steps.length === 0 ? (
              <p className="mt-3 text-sm text-slate-600">No topics in this phase yet.</p>
            ) : (
              <ul className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {phase.steps.map((step) => {
                  const status = normalizeStatus(step.progress_status);
                  const topicTitle = `Topic ${step.topic_id}`;

                  return (
                    <li key={step.id} className="rounded-lg border border-slate-200 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-xs text-slate-500">Priority #{step.priority}</p>
                          <h3 className="mt-1 font-semibold text-slate-900">{topicTitle}</h3>
                        </div>
                        <span
                          className={[
                            "rounded-full px-2.5 py-1 text-xs font-medium capitalize",
                            status === "completed"
                              ? "bg-emerald-100 text-emerald-700"
                              : status === "in_progress"
                                ? "bg-amber-100 text-amber-700"
                                : "bg-slate-100 text-slate-700",
                          ].join(" ")}
                        >
                          {status.replace("_", " ")}
                        </span>
                      </div>

                      <dl className="mt-3 space-y-1 text-sm text-slate-700">
                        <div className="flex justify-between gap-4">
                          <dt>Difficulty</dt>
                          <dd className="font-medium capitalize">{step.difficulty}</dd>
                        </div>
                        <div className="flex justify-between gap-4">
                          <dt>Estimated Time</dt>
                          <dd className="font-medium">{step.estimated_time_hours}h</dd>
                        </div>
                        <div className="flex justify-between gap-4">
                          <dt>Completion Status</dt>
                          <dd className="font-medium capitalize">{status.replace("_", " ")}</dd>
                        </div>
                      </dl>
                    </li>
                  );
                })}
              </ul>
            )}
          </article>
        ))}
      </section>
    </main>
  );
}
