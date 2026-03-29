"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, Compass, Rocket, Target } from "lucide-react";

import RequireAuth from "@/components/auth/RequireAuth";
import SmartLoadingState from "@/components/ui/SmartLoadingState";
import StatusPill from "@/components/ui/StatusPill";
import SurfaceCard from "@/components/ui/SurfaceCard";
import Button from "@/components/ui/Button";
import { getCurrentRoadmapPage } from "@/services/roadmapService";
import { getTopics } from "@/services/topicService";
import type { Roadmap, RoadmapStep } from "@/types/roadmap";
import type { TopicSummary } from "@/types/topic";

function DashboardContent() {
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [topics, setTopics] = useState<TopicSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      setIsLoading(true);
      setError("");
      try {
        const [roadmapPage, topicPage] = await Promise.all([getCurrentRoadmapPage(), getTopics()]);
        setRoadmap(roadmapPage.items[0] ?? null);
        setTopics(topicPage.items);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Unable to load your dashboard right now.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  const topicNames = useMemo(
    () => new Map(topics.map((topic) => [topic.id, topic.name])),
    [topics],
  );

  const steps = roadmap?.steps ?? [];
  const completedSteps = steps.filter((step) => step.progress_status === "completed").length;
  const inProgressSteps = steps.filter((step) => step.progress_status === "in_progress").length;
  const progressPercent = steps.length ? Math.round((completedSteps / steps.length) * 100) : 0;
  const recommendations = [...steps]
    .filter((step) => step.progress_status !== "completed")
    .sort((left, right) => left.priority - right.priority)
    .slice(0, 3);

  if (isLoading) {
    return <SmartLoadingState title="Loading your dashboard" description="We are pulling your latest roadmap and topic context from the backend." />;
  }

  if (error) {
    return (
      <SurfaceCard title="Dashboard unavailable" description="The backend is reachable, but this dashboard request did not complete.">
        <p className="text-sm text-rose-600">{error}</p>
      </SurfaceCard>
    );
  }

  if (!roadmap) {
    return (
      <SurfaceCard
        title="No roadmap yet"
        description="Start a diagnostic to generate your first personalized roadmap."
        actions={
          <Link href="/diagnostic">
            <Button>
              Start diagnostic
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        }
      >
        <p className="text-sm leading-7 text-slate-600 dark:text-slate-300">
          Your backend is connected successfully. The next step is creating a diagnostic session so Learnova AI can recommend the right learning path.
        </p>
      </SurfaceCard>
    );
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        <SurfaceCard title="Progress" description="Completion across your current roadmap.">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-4xl font-semibold text-slate-950 dark:text-slate-50">{progressPercent}%</p>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{completedSteps} of {steps.length} roadmap steps completed</p>
            </div>
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-200">
              <Rocket className="h-6 w-6" />
            </div>
          </div>
        </SurfaceCard>

        <SurfaceCard title="In Progress" description="Topics you are actively working through.">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-4xl font-semibold text-slate-950 dark:text-slate-50">{inProgressSteps}</p>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">Keep momentum on your active concepts.</p>
            </div>
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-200">
              <Compass className="h-6 w-6" />
            </div>
          </div>
        </SurfaceCard>

        <SurfaceCard title="Roadmap Status" description="Current backend generation state.">
          <div className="flex items-end justify-between gap-4">
            <div>
              <StatusPill label={roadmap.status} tone={roadmap.status === "ready" ? "success" : "warning"} />
              <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">Goal #{roadmap.goal_id} • Test #{roadmap.test_id}</p>
            </div>
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-200">
              <Target className="h-6 w-6" />
            </div>
          </div>
        </SurfaceCard>
      </section>

      <SurfaceCard
        title="Recommended Next Topics"
        description="These are the highest-priority roadmap items still open."
        actions={
          <Link href="/roadmap">
            <Button variant="secondary">Open roadmap</Button>
          </Link>
        }
      >
        <div className="grid gap-4 md:grid-cols-3">
          {recommendations.map((step) => (
            <article key={step.id} className="rounded-[26px] border border-slate-200 bg-white/70 p-5 dark:border-slate-700 dark:bg-slate-900/60">
              <StatusPill label={step.progress_status} tone={step.progress_status === "in_progress" ? "warning" : "default"} />
              <h3 className="mt-4 text-lg font-semibold text-slate-950 dark:text-slate-50">{topicNames.get(step.topic_id) ?? `Topic #${step.topic_id}`}</h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">Priority {step.priority} • {step.estimated_time_hours}h estimated</p>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Deadline: {new Date(step.deadline).toLocaleDateString()}</p>
            </article>
          ))}
        </div>
      </SurfaceCard>

      <SurfaceCard
        title="Topic Snapshot"
        description="A quick glance at the first roadmap topics returned by the backend."
        actions={
          <Link href="/diagnostic">
            <Button variant="secondary">Retake diagnostic</Button>
          </Link>
        }
      >
        <div className="grid gap-3 md:grid-cols-2">
          {steps.slice(0, 6).map((step: RoadmapStep) => (
            <div key={step.id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/60">
              <div>
                <p className="font-medium text-slate-900 dark:text-slate-100">{topicNames.get(step.topic_id) ?? `Topic #${step.topic_id}`}</p>
                <p className="text-sm text-slate-500 dark:text-slate-400">Difficulty: {step.difficulty}</p>
              </div>
              <StatusPill label={step.progress_status} tone={step.progress_status === "completed" ? "success" : "default"} />
            </div>
          ))}
        </div>
      </SurfaceCard>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <RequireAuth>
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-teal-700">Dashboard</p>
          <h1 className="text-4xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">Your learning command center</h1>
          <p className="max-w-3xl text-base leading-8 text-slate-600 dark:text-slate-300">
            This page reads directly from the production backend and surfaces roadmap progress, active priorities, and next actions.
          </p>
        </header>
        <DashboardContent />
      </main>
    </RequireAuth>
  );
}
