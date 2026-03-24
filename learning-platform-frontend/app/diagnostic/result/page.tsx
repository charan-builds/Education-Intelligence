"use client";

export const dynamic = "force-dynamic";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import RequireRole from "@/components/auth/RequireRole";
import RoleDashboardLayout from "@/components/layout/RoleDashboardLayout";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import StatusPill from "@/components/ui/StatusPill";
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

function formatProfile(value: string): string {
  return value
    .split("_")
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(" ");
}

export default function DiagnosticResultPage() {
  const [testId, setTestId] = useState<number>(NaN);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const testIdParam = params.get("test_id");
    setTestId(testIdParam ? Number(testIdParam) : NaN);
  }, []);

  const resultQuery = useQuery({
    queryKey: ["diagnostic-result", testId],
    queryFn: () => getDiagnosticResult(testId),
    enabled: Number.isFinite(testId) && testId > 0,
  });

  const topicScores = useMemo(() => {
    const map = resultQuery.data?.topic_scores ?? {};
    return Object.entries(map)
      .map(([topicId, score]) => ({ topicId: Number(topicId), score: Number(score) }))
      .sort((a, b) => a.score - b.score);
  }, [resultQuery.data?.topic_scores]);

  const weakTopics = useMemo(() => topicScores.filter((topic) => topic.score < 70), [topicScores]);
  const strongestTopics = useMemo(() => [...topicScores].sort((a, b) => b.score - a.score).slice(0, 3), [topicScores]);
  const learningProfile = useMemo(
    () => classifyLearningProfile(topicScores.map((topic) => topic.score)),
    [topicScores],
  );
  const averageScore = useMemo(() => {
    if (topicScores.length === 0) {
      return 0;
    }
    const total = topicScores.reduce((sum, topic) => sum + topic.score, 0);
    return Math.round(total / topicScores.length);
  }, [topicScores]);

  return (
    <RequireRole allowedRoles={["student", "teacher", "admin", "super_admin"]}>
      <RoleDashboardLayout
        roleLabel="Diagnostic"
        title="Diagnostic Result"
        description="Topic scores, weak areas, and a lightweight learning-profile interpretation generated from the backend diagnostic result."
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Diagnostic", href: "/diagnostic" },
          { label: "Result" },
        ]}
        navItems={[
          { label: "Goals", href: "/goals/select" },
          { label: "Diagnostic Test", href: "/diagnostic/test" },
          { label: "Roadmap", href: "/roadmap/view" },
          { label: "Progress", href: "/progress" },
        ]}
        actions={
          <div className="flex flex-wrap gap-3">
            <Link href="/goals/select" className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
              New Diagnostic
            </Link>
            <Link href="/roadmap/view" className="rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-400">
              View Roadmap
            </Link>
          </div>
        }
      >
        {!Number.isFinite(testId) || testId <= 0 ? (
          <SurfaceCard title="Missing Test Reference" description="This page needs a valid diagnostic session ID to load results.">
            <p className="text-sm text-slate-600">Open this page using a valid `test_id` query parameter from the diagnostic flow.</p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link href="/goals/select" className="rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-400">
                Start New Diagnostic
              </Link>
              <Link href="/dashboard/student" className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                Student Dashboard
              </Link>
            </div>
          </SurfaceCard>
        ) : null}

        {Number.isFinite(testId) && testId > 0 && (
          <>
            {resultQuery.isLoading ? <p className="text-slate-600">Loading diagnostic result...</p> : null}
            {resultQuery.isError ? (
              <SurfaceCard title="Result Unavailable" description="The backend did not return a diagnostic result for this session.">
                <p className="text-sm text-red-600">Failed to fetch diagnostic result.</p>
                <div className="mt-4 flex flex-wrap gap-3">
                  <Link href="/goals/select" className="rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-400">
                    Start New Diagnostic
                  </Link>
                  <Link href="/diagnostic/test" className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                    Return to Diagnostic
                  </Link>
                </div>
              </SurfaceCard>
            ) : null}

            {!resultQuery.isLoading && !resultQuery.isError ? (
              <>
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <MetricCard title="Scored Topics" value={topicScores.length} description="Topic score entries returned by the backend engine." tone="info" />
                  <MetricCard title="Average Score" value={`${averageScore}%`} description="Blended performance across evaluated topics." tone="success" />
                  <MetricCard title="Weak Topics" value={weakTopics.length} description="Topics below the current intervention threshold." tone="warning" />
                  <MetricCard title="Learning Profile" value={formatProfile(learningProfile)} description="Frontend interpretation of the score distribution." />
                </div>

                <div className="grid gap-6 xl:grid-cols-[1.35fr_1fr]">
                  <SurfaceCard title="Topic Score Breakdown" description="Lowest-scoring topics appear first to make intervention priorities easier to spot.">
                    {topicScores.length === 0 ? (
                      <p className="text-slate-600">No topic score data is available for this diagnostic yet.</p>
                    ) : (
                      <ul className="space-y-3">
                        {topicScores.map((topic) => {
                          const tone = topic.score >= 70 ? "success" : topic.score >= 50 ? "warning" : "default";
                          const label = topic.score >= 70 ? "mastered" : topic.score >= 50 ? "needs practice" : "beginner";
                          return (
                            <li key={topic.topicId} className="rounded-2xl border border-slate-200 px-4 py-4">
                              <div className="flex flex-wrap items-center justify-between gap-3">
                                <div>
                                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Topic</p>
                                  <p className="mt-1 text-sm font-semibold text-slate-900">Topic #{topic.topicId}</p>
                                </div>
                                <div className="flex items-center gap-3">
                                  <StatusPill label={label} tone={tone} />
                                  <span className="text-sm font-semibold text-slate-900">{topic.score.toFixed(1)}%</span>
                                </div>
                              </div>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </SurfaceCard>

                  <div className="space-y-6">
                    <SurfaceCard title="Priority Follow-Up" description="These are the immediate topics that should influence roadmap generation and review.">
                      {weakTopics.length === 0 ? (
                        <p className="text-sm text-emerald-700">No weak topics detected in this diagnostic session.</p>
                      ) : (
                        <ul className="space-y-3">
                          {weakTopics.map((topic) => (
                            <li key={topic.topicId} className="rounded-2xl border border-rose-100 bg-rose-50 px-4 py-3">
                              <p className="text-sm font-semibold text-rose-800">Topic #{topic.topicId}</p>
                              <p className="mt-1 text-sm text-rose-700">{topic.score.toFixed(1)}% mastery</p>
                            </li>
                          ))}
                        </ul>
                      )}
                    </SurfaceCard>

                    <SurfaceCard title="Strongest Areas" description="Helpful for balancing roadmap intensity and mentor guidance.">
                      {strongestTopics.length === 0 ? (
                        <p className="text-sm text-slate-600">No strong topic signals yet.</p>
                      ) : (
                        <ul className="space-y-3">
                          {strongestTopics.map((topic) => (
                            <li key={topic.topicId} className="rounded-2xl border border-emerald-100 bg-emerald-50 px-4 py-3">
                              <p className="text-sm font-semibold text-emerald-800">Topic #{topic.topicId}</p>
                              <p className="mt-1 text-sm text-emerald-700">{topic.score.toFixed(1)}% mastery</p>
                            </li>
                          ))}
                        </ul>
                      )}
                    </SurfaceCard>
                  </div>
                </div>
              </>
            ) : null}
          </>
        )}
      </RoleDashboardLayout>
    </RequireRole>
  );
}
