"use client";

export const dynamic = "force-dynamic";

import { useMemo } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { getDiagnosticResult } from "@/services/diagnosticService";

function classifyLearningProfile(scores: number[]): string {
  if (scores.length === 0) {
    return "balanced";
  }

  const avg = scores.reduce((sum, value) => sum + value, 0) / scores.length;
  const weakCount = scores.filter((score) => score < 50).length;
  const strongCount = scores.filter((score) => score > 75).length;

  if (avg >= 75 && strongCount >= Math.ceil(scores.length / 2)) {
    return "concept_focused";
  }
  if (weakCount >= Math.ceil(scores.length / 2)) {
    return "practice_focused";
  }
  if (avg < 60) {
    return "slow_deep_learner";
  }
  return "balanced";
}

export default function DiagnosticResultPage() {
  const searchParams = useSearchParams();
  const testIdParam = searchParams.get("test_id");
  const testId = testIdParam ? Number(testIdParam) : NaN;

  const resultQuery = useQuery({
    queryKey: ["diagnostic-result", testId],
    queryFn: () => getDiagnosticResult(testId),
    enabled: Number.isFinite(testId) && testId > 0,
  });

  const topicScores = useMemo(() => {
    const map = resultQuery.data?.topic_scores ?? {};
    return Object.entries(map)
      .map(([topicId, score]) => ({ topicId: Number(topicId), score: Number(score) }))
      .sort((a, b) => a.topicId - b.topicId);
  }, [resultQuery.data?.topic_scores]);

  const weakTopics = useMemo(() => topicScores.filter((topic) => topic.score < 70), [topicScores]);

  const learningProfile = useMemo(() => {
    const values = topicScores.map((topic) => topic.score);
    return classifyLearningProfile(values);
  }, [topicScores]);

  if (!Number.isFinite(testId) || testId <= 0) {
    return (
      <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
        <h1 className="text-3xl font-semibold tracking-tight">Diagnostic Result</h1>
        <p className="mt-3 text-slate-600">Missing or invalid `test_id` query parameter.</p>
        <Link href="/diagnostic/test" className="mt-4 inline-block rounded-lg bg-brand-600 px-4 py-2 text-white">
          Go to Diagnostic Test
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Diagnostic Result</h1>
          <p className="mt-2 text-slate-600">Test ID: {testId}</p>
        </div>
        <Link href="/roadmap/view" className="rounded-lg bg-brand-600 px-4 py-2 text-white hover:bg-brand-700">
          View Roadmap
        </Link>
      </div>

      {resultQuery.isLoading && <p className="mt-8 text-slate-600">Loading diagnostic result...</p>}
      {resultQuery.isError && <p className="mt-8 text-red-600">Failed to fetch diagnostic result.</p>}

      {!resultQuery.isLoading && !resultQuery.isError && (
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Total Topics</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{topicScores.length}</p>
          </article>
          <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Weak Topics</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{weakTopics.length}</p>
          </article>
          <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Learning Profile</p>
            <p className="mt-2 text-2xl font-semibold capitalize text-slate-900">
              {learningProfile.replaceAll("_", " ")}
            </p>
          </article>
        </div>
      )}

      {!resultQuery.isLoading && !resultQuery.isError && (
        <section className="mt-8 grid gap-4 lg:grid-cols-2">
          <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Topic Scores</h2>
            {topicScores.length === 0 ? (
              <p className="mt-4 text-slate-600">No topic score data available.</p>
            ) : (
              <ul className="mt-4 space-y-2">
                {topicScores.map((topic) => (
                  <li key={topic.topicId} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2">
                    <span className="text-sm font-medium text-slate-800">Topic #{topic.topicId}</span>
                    <span className="text-sm text-slate-700">{topic.score.toFixed(1)}%</span>
                  </li>
                ))}
              </ul>
            )}
          </article>

          <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Weak Topics</h2>
            {weakTopics.length === 0 ? (
              <p className="mt-4 text-emerald-700">No weak topics detected.</p>
            ) : (
              <ul className="mt-4 space-y-2">
                {weakTopics.map((topic) => (
                  <li key={topic.topicId} className="rounded-lg border border-rose-100 bg-rose-50 px-3 py-2 text-sm">
                    <span className="font-medium text-rose-800">Topic #{topic.topicId}</span>
                    <span className="ml-2 text-rose-700">{topic.score.toFixed(1)}%</span>
                  </li>
                ))}
              </ul>
            )}
          </article>
        </section>
      )}
    </main>
  );
}
