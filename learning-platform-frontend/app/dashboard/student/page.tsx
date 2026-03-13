"use client";

export const dynamic = "force-dynamic";

import { useMemo } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import MentorNotifications from "@/components/MentorNotifications";
import MentorSuggestions from "@/components/MentorSuggestions";
import MentorProgressAnalysis from "@/components/MentorProgressAnalysis";
import NextTopicCard from "@/components/student/NextTopicCard";
import ProgressCard from "@/components/student/ProgressCard";
import RoadmapProgress from "@/components/student/RoadmapProgress";
import WeakTopicsCard from "@/components/student/WeakTopicsCard";
import { useAuth } from "@/hooks/useAuth";
import { getUserRoadmap } from "@/services/roadmapService";

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

export default function StudentDashboardPage() {
  const { user, isAuthenticated } = useAuth();

  const roadmapQuery = useQuery({
    queryKey: ["student-roadmap", user?.user_id],
    queryFn: async () => {
      if (!user?.user_id) {
        throw new Error("Missing user id");
      }
      return getUserRoadmap(user.user_id);
    },
    enabled: Boolean(isAuthenticated && user?.user_id),
  });

  const currentRoadmap = roadmapQuery.data?.items?.[0] ?? null;

  const orderedSteps = useMemo(
    () => [...(currentRoadmap?.steps ?? [])].sort((a, b) => a.priority - b.priority),
    [currentRoadmap?.steps],
  );

  const summary = useMemo(() => {
    const totalTopics = orderedSteps.length;
    const completedTopics = orderedSteps.filter((step) => normalizeStatus(step.progress_status) === "completed").length;
    const currentStep =
      orderedSteps.find((step) => normalizeStatus(step.progress_status) === "in_progress") ??
      orderedSteps.find((step) => normalizeStatus(step.progress_status) === "pending") ??
      null;
    const nextRecommended = orderedSteps.find((step) => normalizeStatus(step.progress_status) === "pending") ?? null;

    const weakTopics = orderedSteps
      .filter((step) => {
        const state = normalizeStatus(step.progress_status);
        return state !== "completed" && ["hard", "expert"].includes(step.difficulty.toLowerCase());
      })
      .map((step) => ({
        topicId: step.topic_id,
        difficulty: step.difficulty,
        status: normalizeStatus(step.progress_status),
      }));

    return {
      totalTopics,
      completedTopics,
      currentStep,
      nextRecommended,
      weakTopics,
    };
  }, [orderedSteps]);

  if (!isAuthenticated) {
    return (
      <main className="mx-auto min-h-screen max-w-6xl p-8">
        <h1 className="text-3xl font-semibold">Student Dashboard</h1>
        <p className="mt-2 text-slate-600">Please login to view your dashboard.</p>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <div className="mx-auto grid min-h-screen max-w-7xl grid-cols-1 lg:grid-cols-[240px_1fr]">
        <aside className="border-r border-slate-200 bg-white p-5">
          <h2 className="text-xl font-semibold text-slate-900">LearnIQ</h2>
          <nav className="mt-6 space-y-2 text-sm">
            <Link className="block rounded-md bg-slate-100 px-3 py-2 font-medium text-slate-900" href="/dashboard/student">
              Dashboard
            </Link>
            <Link className="block rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/diagnostic/test">
              Diagnostic Test
            </Link>
            <Link className="block rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/roadmap/view">
              Roadmap View
            </Link>
          </nav>
        </aside>

        <div>
          <header className="border-b border-slate-200 bg-white px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-semibold text-slate-900">Student Dashboard</h1>
                <p className="text-sm text-slate-600">Track your roadmap progress and learning priorities</p>
              </div>
              <div className="text-right text-sm text-slate-600">
                <p>User ID: {user?.user_id ?? "-"}</p>
                <p className="capitalize">Role: {user?.role ?? "student"}</p>
              </div>
            </div>
          </header>

          <main className="space-y-6 p-6">
            {roadmapQuery.isLoading && <p className="text-slate-600">Loading roadmap...</p>}
            {roadmapQuery.isError && <p className="text-red-600">Failed to load roadmap.</p>}

            {!roadmapQuery.isLoading && !roadmapQuery.isError && (
              <>
                <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <ProgressCard title="Total Topics" value={summary.totalTopics} subtitle="All roadmap topics" />
                  <ProgressCard
                    title="Completed Topics"
                    value={summary.completedTopics}
                    subtitle={`${summary.totalTopics > 0 ? Math.round((summary.completedTopics / summary.totalTopics) * 100) : 0}% complete`}
                  />
                  <ProgressCard
                    title="Current Topic"
                    value={summary.currentStep ? `Topic #${summary.currentStep.topic_id}` : "Not started"}
                    subtitle={summary.currentStep ? `Priority #${summary.currentStep.priority}` : "Start your roadmap"}
                  />
                  <ProgressCard
                    title="Recommended Next"
                    value={summary.nextRecommended ? `Topic #${summary.nextRecommended.topic_id}` : "None"}
                    subtitle={summary.nextRecommended ? `Difficulty: ${summary.nextRecommended.difficulty}` : "No pending topics"}
                  />
                </section>

                <section className="grid gap-4 xl:grid-cols-3">
                  <div className="xl:col-span-2">
                    <RoadmapProgress
                      totalTopics={summary.totalTopics}
                      completedTopics={summary.completedTopics}
                      currentTopic={summary.currentStep ? `Topic #${summary.currentStep.topic_id}` : "Not started"}
                    />
                  </div>
                  <NextTopicCard
                    topicLabel={summary.nextRecommended ? `Topic #${summary.nextRecommended.topic_id}` : "No pending topics"}
                    difficulty={summary.nextRecommended?.difficulty ?? "n/a"}
                    deadline={
                      summary.nextRecommended?.deadline
                        ? new Date(summary.nextRecommended.deadline).toLocaleDateString()
                        : undefined
                    }
                  />
                </section>

                <section className="grid gap-4 xl:grid-cols-3">
                  <div className="space-y-4 xl:col-span-1">
                    <WeakTopicsCard weakTopics={summary.weakTopics} />
                    <MentorSuggestions />
                    <MentorNotifications />
                    <MentorProgressAnalysis />
                  </div>

                  <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm xl:col-span-2">
                    <h2 className="text-lg font-semibold text-slate-900">Roadmap Topics</h2>
                    {orderedSteps.length === 0 ? (
                      <p className="mt-3 text-sm text-slate-600">No roadmap topics found.</p>
                    ) : (
                      <ul className="mt-4 space-y-2">
                        {orderedSteps.map((step) => {
                          const status = normalizeStatus(step.progress_status);
                          return (
                            <li key={step.id} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2">
                              <div>
                                <p className="text-sm font-medium text-slate-900">Topic #{step.topic_id}</p>
                                <p className="text-xs text-slate-600">
                                  Priority #{step.priority} • {step.difficulty}
                                </p>
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
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </div>
                </section>
              </>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
