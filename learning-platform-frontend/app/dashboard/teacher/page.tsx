"use client";

export const dynamic = "force-dynamic";

import { useMemo } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";

import { getUserRoadmap } from "@/services/roadmapService";
import { getUsers } from "@/services/userService";

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

export default function TeacherDashboardPage() {
  const usersQuery = useQuery({
    queryKey: ["teacher-users"],
    queryFn: getUsers,
  });

  const students = useMemo(
    () => (usersQuery.data?.items ?? []).filter((user) => user.role === "student"),
    [usersQuery.data?.items],
  );

  const roadmapQueries = useQueries({
    queries: students.map((student) => ({
      queryKey: ["teacher-student-roadmap", student.id],
      queryFn: () => getUserRoadmap(student.id),
      enabled: students.length > 0,
    })),
  });

  const rows = useMemo(() => {
    return students.map((student, index) => {
      const roadmapData = roadmapQueries[index]?.data;
      const steps = roadmapData?.items?.[0]?.steps ?? [];
      const total = steps.length;
      const completed = steps.filter((step) => normalizeStatus(step.progress_status) === "completed").length;
      const inProgress = steps.filter((step) => normalizeStatus(step.progress_status) === "in_progress").length;
      const progressPercent = total > 0 ? Math.round((completed / total) * 100) : 0;

      const masteryScore =
        total > 0
          ? Math.round(
              steps.reduce((acc, step) => {
                if (normalizeStatus(step.progress_status) === "completed") {
                  return acc + 100;
                }
                if (normalizeStatus(step.progress_status) === "in_progress") {
                  return acc + 60;
                }
                return acc + 20;
              }, 0) / total,
            )
          : 0;

      return {
        studentId: student.id,
        email: student.email,
        progressPercent,
        completed,
        total,
        inProgress,
        masteryScore,
        diagnosticScore: roadmapData?.items?.length ? `${masteryScore}%` : "N/A",
      };
    });
  }, [students, roadmapQueries]);

  const loadingRoadmaps = roadmapQueries.some((query) => query.isLoading);
  const roadmapError = roadmapQueries.some((query) => query.isError);

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <h1 className="text-3xl font-semibold tracking-tight">Teacher Dashboard</h1>
      <p className="mt-2 text-slate-600">Monitor student progress, topic mastery, and diagnostic scores.</p>

      <section className="mt-8 grid gap-4 md:grid-cols-3">
        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Students</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">{students.length}</p>
        </article>

        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Avg Progress</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">
            {rows.length > 0 ? Math.round(rows.reduce((sum, row) => sum + row.progressPercent, 0) / rows.length) : 0}%
          </p>
        </article>

        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Avg Topic Mastery</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">
            {rows.length > 0 ? Math.round(rows.reduce((sum, row) => sum + row.masteryScore, 0) / rows.length) : 0}%
          </p>
        </article>
      </section>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Student Overview</h2>

        {usersQuery.isLoading && <p className="mt-4 text-slate-600">Loading students...</p>}
        {usersQuery.isError && <p className="mt-4 text-red-600">Failed to load users.</p>}
        {!usersQuery.isLoading && !usersQuery.isError && loadingRoadmaps && (
          <p className="mt-4 text-slate-600">Loading student roadmaps...</p>
        )}
        {roadmapError && <p className="mt-4 text-red-600">Failed to load one or more student roadmaps.</p>}

        {!usersQuery.isLoading && !usersQuery.isError && students.length === 0 && (
          <p className="mt-4 text-slate-600">No students found in this tenant.</p>
        )}

        {rows.length > 0 && (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Student</th>
                  <th className="px-4 py-3 font-medium">Progress</th>
                  <th className="px-4 py-3 font-medium">Topic Mastery</th>
                  <th className="px-4 py-3 font-medium">Diagnostic Scores</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white text-slate-800">
                {rows.map((row) => (
                  <tr key={row.studentId}>
                    <td className="px-4 py-3">{row.email}</td>
                    <td className="px-4 py-3">
                      {row.progressPercent}% ({row.completed}/{row.total})
                    </td>
                    <td className="px-4 py-3">{row.masteryScore}%</td>
                    <td className="px-4 py-3">{row.diagnosticScore}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
