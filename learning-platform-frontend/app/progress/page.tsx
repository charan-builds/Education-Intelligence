"use client";

export const dynamic = "force-dynamic";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

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

const PIE_COLORS = ["#10b981", "#f59e0b", "#94a3b8"];

export default function ProgressPage() {
  const { user, isAuthenticated } = useAuth();

  const roadmapQuery = useQuery({
    queryKey: ["progress-roadmap", user?.user_id],
    queryFn: async () => {
      if (!user?.user_id) {
        throw new Error("Missing user id");
      }
      return getUserRoadmap(user.user_id);
    },
    enabled: Boolean(isAuthenticated && user?.user_id),
  });

  const steps = useMemo(() => {
    const roadmap = roadmapQuery.data?.items?.[0];
    return [...(roadmap?.steps ?? [])].sort((a, b) => a.priority - b.priority);
  }, [roadmapQuery.data?.items]);

  const summary = useMemo(() => {
    const totalTopics = steps.length;
    const completedTopics = steps.filter((step) => normalizeStatus(step.progress_status) === "completed").length;
    const inProgressTopics = steps.filter((step) => normalizeStatus(step.progress_status) === "in_progress").length;
    const pendingTopics = steps.filter((step) => normalizeStatus(step.progress_status) === "pending").length;

    const roadmapProgress = totalTopics > 0 ? Math.round((completedTopics / totalTopics) * 100) : 0;

    // Deterministic streak approximation for MVP: contiguous completed steps from start.
    let streak = 0;
    for (const step of steps) {
      if (normalizeStatus(step.progress_status) === "completed") {
        streak += 1;
      } else {
        break;
      }
    }

    return {
      totalTopics,
      completedTopics,
      inProgressTopics,
      pendingTopics,
      roadmapProgress,
      learningStreak: streak,
    };
  }, [steps]);

  const progressLineData = useMemo(
    () =>
      steps.map((step, index) => {
        const completedUntilNow = steps.slice(0, index + 1).filter((s) => normalizeStatus(s.progress_status) === "completed").length;
        const percent = index + 1 > 0 ? Math.round((completedUntilNow / (index + 1)) * 100) : 0;
        return {
          topic: `T${step.topic_id}`,
          progress: percent,
        };
      }),
    [steps],
  );

  const difficultyBarData = useMemo(() => {
    const bucket = { easy: 0, medium: 0, hard: 0, expert: 0 };
    for (const step of steps) {
      const key = step.difficulty.toLowerCase();
      if (key in bucket) {
        bucket[key as keyof typeof bucket] += 1;
      }
    }
    return [
      { difficulty: "easy", count: bucket.easy },
      { difficulty: "medium", count: bucket.medium },
      { difficulty: "hard", count: bucket.hard },
      { difficulty: "expert", count: bucket.expert },
    ];
  }, [steps]);

  const statusPieData = useMemo(
    () => [
      { name: "Completed", value: summary.completedTopics },
      { name: "In Progress", value: summary.inProgressTopics },
      { name: "Pending", value: summary.pendingTopics },
    ],
    [summary.completedTopics, summary.inProgressTopics, summary.pendingTopics],
  );

  if (!isAuthenticated) {
    return (
      <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
        <h1 className="text-3xl font-semibold tracking-tight">Progress Tracking</h1>
        <p className="mt-3 text-slate-600">Please login to view your progress.</p>
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <h1 className="text-3xl font-semibold tracking-tight">Progress Tracking</h1>
      <p className="mt-2 text-slate-600">Topics completed, learning streak, and roadmap progress.</p>

      {roadmapQuery.isLoading && <p className="mt-8 text-slate-600">Loading progress data...</p>}
      {roadmapQuery.isError && <p className="mt-8 text-red-600">Failed to load progress data.</p>}

      {!roadmapQuery.isLoading && !roadmapQuery.isError && (
        <>
          <section className="mt-8 grid gap-4 md:grid-cols-3">
            <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">Topics Completed</p>
              <p className="mt-2 text-3xl font-semibold text-slate-900">{summary.completedTopics}</p>
              <p className="mt-1 text-sm text-slate-600">out of {summary.totalTopics} topics</p>
            </article>

            <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">Learning Streak</p>
              <p className="mt-2 text-3xl font-semibold text-slate-900">{summary.learningStreak}</p>
              <p className="mt-1 text-sm text-slate-600">consecutive completed topics</p>
            </article>

            <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">Roadmap Progress</p>
              <p className="mt-2 text-3xl font-semibold text-slate-900">{summary.roadmapProgress}%</p>
              <p className="mt-1 text-sm text-slate-600">overall completion</p>
            </article>
          </section>

          <section className="mt-8 grid gap-4 lg:grid-cols-2">
            <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Roadmap Progress Trend</h2>
              <div className="mt-4 h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={progressLineData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="topic" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="progress" stroke="#2563eb" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Topic Status Breakdown</h2>
              <div className="mt-4 h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={statusPieData} dataKey="value" nameKey="name" outerRadius={100} label>
                      {statusPieData.map((_, index) => (
                        <Cell key={`status-cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </article>
          </section>

          <section className="mt-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Difficulty Distribution</h2>
            <div className="mt-4 h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={difficultyBarData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="difficulty" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#0ea5e9" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>
        </>
      )}
    </main>
  );
}
