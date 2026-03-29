"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { CalendarClock, Sparkles } from "lucide-react";

import RequireAuth from "@/components/auth/RequireAuth";
import Button from "@/components/ui/Button";
import SmartLoadingState from "@/components/ui/SmartLoadingState";
import StatusPill from "@/components/ui/StatusPill";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { getCurrentRoadmapPage } from "@/services/roadmapService";
import { getTopics } from "@/services/topicService";
import type { Roadmap } from "@/types/roadmap";
import type { TopicSummary } from "@/types/topic";

function RoadmapContent() {
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [topics, setTopics] = useState<TopicSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadRoadmap() {
      setIsLoading(true);
      setError("");
      try {
        const [roadmapPage, topicPage] = await Promise.all([getCurrentRoadmapPage(), getTopics()]);
        setRoadmap(roadmapPage.items[0] ?? null);
        setTopics(topicPage.items);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Unable to load your roadmap.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadRoadmap();
  }, []);

  const topicNames = useMemo(() => new Map(topics.map((topic) => [topic.id, topic.name])), [topics]);

  if (isLoading) {
    return <SmartLoadingState title="Loading roadmap" description="We are pulling your latest roadmap, deadlines, and learning priorities from the backend." />;
  }

  if (error) {
    return (
      <SurfaceCard title="Roadmap unavailable" description="The backend request did not complete successfully.">
        <p className="text-sm text-rose-600">{error}</p>
      </SurfaceCard>
    );
  }

  if (!roadmap) {
    return (
      <SurfaceCard
        title="No roadmap generated yet"
        description="Run a diagnostic first so the roadmap engine has the right input."
        actions={
          <Link href="/diagnostic">
            <Button>Open diagnostic</Button>
          </Link>
        }
      >
        <p className="text-sm leading-7 text-slate-600 dark:text-slate-300">
          Once a diagnostic is completed, this page will fetch your roadmap from `GET /roadmap/view` and show deadlines, progress, and recommended next topics.
        </p>
      </SurfaceCard>
    );
  }

  return (
    <div className="space-y-6">
      <SurfaceCard
        title="Roadmap Overview"
        description={`Roadmap #${roadmap.id} for goal #${roadmap.goal_id}`}
        actions={<StatusPill label={roadmap.status} tone={roadmap.status === "ready" ? "success" : "warning"} />}
      >
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-[26px] border border-slate-200 bg-white/80 p-5 dark:border-slate-700 dark:bg-slate-900/60">
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Generated</p>
            <p className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">
              {new Date(roadmap.generated_at).toLocaleString()}
            </p>
          </div>
          <div className="rounded-[26px] border border-slate-200 bg-white/80 p-5 dark:border-slate-700 dark:bg-slate-900/60">
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Total steps</p>
            <p className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">{roadmap.steps.length}</p>
          </div>
          <div className="rounded-[26px] border border-slate-200 bg-white/80 p-5 dark:border-slate-700 dark:bg-slate-900/60">
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Completed</p>
            <p className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">
              {roadmap.steps.filter((step) => step.progress_status === "completed").length}
            </p>
          </div>
        </div>
      </SurfaceCard>

      <SurfaceCard
        title="Roadmap Steps"
        description="Topics, priorities, deadlines, and progress state returned by the backend roadmap service."
      >
        <div className="space-y-4">
          {roadmap.steps.map((step) => (
            <article key={step.id} className="rounded-[28px] border border-slate-200 bg-white/75 p-5 dark:border-slate-700 dark:bg-slate-900/60">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <h3 className="text-xl font-semibold text-slate-950 dark:text-slate-50">{topicNames.get(step.topic_id) ?? `Topic #${step.topic_id}`}</h3>
                  <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
                    Phase: {step.phase ?? "Core"} • Priority {step.priority} • {step.estimated_time_hours}h estimated • Difficulty {step.difficulty}
                  </p>
                </div>
                <StatusPill
                  label={step.progress_status}
                  tone={
                    step.progress_status === "completed"
                      ? "success"
                      : step.progress_status === "in_progress"
                        ? "warning"
                        : "default"
                  }
                />
              </div>

              <div className="mt-4 flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                <CalendarClock className="h-4 w-4" />
                <span>Deadline: {new Date(step.deadline).toLocaleDateString()}</span>
              </div>
            </article>
          ))}
        </div>
      </SurfaceCard>

      <SurfaceCard title="Recommended next actions" description="Use these to keep the learner moving without friction.">
        <div className="grid gap-4 md:grid-cols-3">
          {[...roadmap.steps]
            .filter((step) => step.progress_status !== "completed")
            .sort((left, right) => left.priority - right.priority)
            .slice(0, 3)
            .map((step) => (
              <div key={step.id} className="rounded-[26px] border border-slate-200 bg-slate-50/90 p-5 dark:border-slate-700 dark:bg-slate-900/60">
                <div className="flex items-center gap-2 text-sm font-semibold text-teal-700 dark:text-teal-200">
                  <Sparkles className="h-4 w-4" />
                  Next recommendation
                </div>
                <h3 className="mt-3 text-lg font-semibold text-slate-950 dark:text-slate-50">{topicNames.get(step.topic_id) ?? `Topic #${step.topic_id}`}</h3>
                <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
                  Prioritize this topic next based on roadmap ordering and current completion state.
                </p>
              </div>
            ))}
        </div>
      </SurfaceCard>
    </div>
  );
}

export default function RoadmapPage() {
  return (
    <RequireAuth>
      <main className="mx-auto max-w-5xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-teal-700">Roadmap</p>
          <h1 className="text-4xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">Your personalized roadmap</h1>
          <p className="max-w-3xl text-base leading-8 text-slate-600 dark:text-slate-300">
            This view reads your latest roadmap directly from the backend and turns it into a clear execution plan with progress and deadlines.
          </p>
        </header>
        <RoadmapContent />
      </main>
    </RequireAuth>
  );
}
