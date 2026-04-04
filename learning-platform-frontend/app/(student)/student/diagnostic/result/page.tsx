"use client";

export const dynamic = "force-dynamic";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Gauge, Sparkles, Target, TriangleAlert } from "lucide-react";

import RequireRole from "@/components/auth/RequireRole";
import RoleDashboardLayout from "@/components/layout/RoleDashboardLayout";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import StatusPill from "@/components/ui/StatusPill";
import Button from "@/components/ui/Button";
import { generateRoadmap } from "@/services/roadmapService";
import { getDiagnosticResult } from "@/services/diagnosticService";
import { normalizeRoadmapGenerationStatus } from "@/hooks/useDashboard";
import { useAuth } from "@/hooks/useAuth";
import { getLearnerRoutes } from "@/utils/appRoutes";

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

export default function StudentDiagnosticResultPage() {
  const { role } = useAuth();
  const learnerRoutes = getLearnerRoutes(role);
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
    refetchInterval: (query) => {
      const roadmap = query.state.data?.roadmap;
      return roadmap && normalizeRoadmapGenerationStatus(roadmap.status) === "generating" ? 2500 : false;
    },
  });

  const topicScores = useMemo(() => {
    const map = resultQuery.data?.topic_scores ?? {};
    return Object.entries(map)
      .map(([topicId, score]) => ({ topicId: Number(topicId), score: Number(score) }))
      .sort((a, b) => a.score - b.score);
  }, [resultQuery.data?.topic_scores]);

  const weakTopics = useMemo(() => topicScores.filter((topic) => topic.score < 70), [topicScores]);
  const foundationGapTopicIds = resultQuery.data?.foundation_gap_topic_ids ?? [];
  const recommendationLevels = resultQuery.data?.recommendation_levels ?? {};
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
  const roadmap = resultQuery.data?.roadmap ?? null;
  const roadmapStatus = normalizeRoadmapGenerationStatus(roadmap?.status);

  return (
    <RequireRole allowedRoles={["student", "independent_learner", "teacher", "admin", "super_admin"]}>
      <RoleDashboardLayout
        roleLabel="Diagnostic"
        title="Diagnostic Result"
        description="Topic scores, weak areas, and a lightweight learning-profile interpretation generated from the backend diagnostic result."
        breadcrumbs={[
          { label: "Dashboard", href: learnerRoutes.dashboard },
          { label: "Diagnostic", href: learnerRoutes.diagnostic },
          { label: "Result" },
        ]}
        navItems={[
          { label: "Goals", href: learnerRoutes.goals },
          { label: "Diagnostic", href: learnerRoutes.diagnostic },
          { label: "Roadmap", href: learnerRoutes.roadmap },
          { label: "Progress", href: learnerRoutes.progress },
        ]}
        actions={
          <div className="flex flex-wrap gap-3">
            <Link href={learnerRoutes.goals} className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
              New Diagnostic
            </Link>
            <Link href={learnerRoutes.roadmap} className="rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-400">
              Continue Journey
            </Link>
          </div>
        }
      >
        {!Number.isFinite(testId) || testId <= 0 ? (
          <SurfaceCard title="Missing Test Reference" description="This page needs a valid diagnostic session ID to load results.">
            <p className="text-sm text-slate-600">Open this page using a valid `test_id` query parameter from the diagnostic flow.</p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link href={learnerRoutes.goals} className="rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-400">
                Start New Diagnostic
              </Link>
              <Link href={learnerRoutes.dashboard} className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                Learning Dashboard
              </Link>
            </div>
          </SurfaceCard>
        ) : null}

        {Number.isFinite(testId) && testId > 0 ? (
          <>
            {resultQuery.isLoading ? <p className="text-slate-600">Loading diagnostic result...</p> : null}
            {resultQuery.isError ? (
              <SurfaceCard title="Result Unavailable" description="The backend did not return a diagnostic result for this session.">
                <p className="text-sm text-red-600">Failed to fetch diagnostic result.</p>
                <div className="mt-4 flex flex-wrap gap-3">
                  <Link href={learnerRoutes.goals} className="rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-400">
                    Start New Diagnostic
                  </Link>
                  <Link href={learnerRoutes.diagnostic} className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
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

                <SurfaceCard title="Roadmap generation" description="The platform now keeps roadmap creation in one tracked lifecycle before moving you forward.">
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-3">
                        <StatusPill
                          label={roadmapStatus}
                          tone={roadmapStatus === "ready" ? "success" : roadmapStatus === "failed" ? "warning" : "default"}
                        />
                        <p className="text-sm text-slate-600">
                          {roadmapStatus === "ready"
                            ? "Your roadmap is ready. You can move straight into the next step."
                            : roadmapStatus === "failed"
                              ? roadmap?.error_message ?? "Roadmap generation failed. Try again to restart it."
                              : "Your roadmap is being generated automatically from this diagnostic."}
                        </p>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-3">
                      {roadmapStatus === "failed" ? (
                        <Button
                          onClick={async () => {
                            if (!resultQuery.data?.roadmap) {
                              return;
                            }
                            await generateRoadmap(resultQuery.data.roadmap.goal_id, testId);
                            await resultQuery.refetch();
                          }}
                        >
                          Generate roadmap
                        </Button>
                      ) : null}
                      <Link href={learnerRoutes.roadmap} className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                        Open roadmap
                      </Link>
                    </div>
                  </div>
                </SurfaceCard>

                <section className="grid gap-4 lg:grid-cols-3">
                  <div className="story-card">
                    <div className="flex items-start gap-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-200">
                        <Gauge className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Current read</p>
                        <p className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">{formatProfile(learningProfile)}</p>
                        <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">A quick interpretation of your current score distribution across the evaluated topics.</p>
                      </div>
                    </div>
                  </div>
                  <div className="story-card">
                    <div className="flex items-start gap-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-200">
                        <TriangleAlert className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Immediate attention</p>
                        <p className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">{weakTopics.length} weak topics</p>
                        <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">These topics should drive your next practice, mentor prompts, and roadmap follow-up.</p>
                      </div>
                    </div>
                  </div>
                  <div className="story-card">
                    <div className="flex items-start gap-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-200">
                        <CheckCircle2 className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Confidence zone</p>
                        <p className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">{strongestTopics.length} strong areas</p>
                        <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">Use your strongest topics to build confidence while you recover the weaker parts of the path.</p>
                      </div>
                    </div>
                  </div>
                </section>

                <div className="grid gap-6 xl:grid-cols-[1.35fr_1fr]">
                  <SurfaceCard
                    title="Topic Score Breakdown"
                    description="Lowest-scoring topics appear first to make intervention priorities easier to spot."
                    className="bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.12),_transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.99),rgba(248,250,252,0.96))] dark:bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.1),_transparent_34%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))]"
                  >
                    {topicScores.length === 0 ? (
                      <p className="text-slate-600">No topic score data is available for this diagnostic yet.</p>
                    ) : (
                      <ul className="space-y-3">
                        {topicScores.map((topic) => {
                          const tone = topic.score >= 70 ? "success" : topic.score >= 50 ? "warning" : "default";
                          const label = topic.score >= 70 ? "mastered" : topic.score >= 50 ? "needs practice" : "beginner";
                          const scoreWidth = Math.max(8, Math.min(100, topic.score));
                          return (
                            <li key={topic.topicId} className="rounded-[24px] border border-slate-200 bg-white/90 px-4 py-4 shadow-[0_16px_40px_-32px_rgba(15,23,42,0.22)] dark:border-slate-700 dark:bg-slate-950/72">
                              <div className="flex flex-wrap items-center justify-between gap-3">
                                <div>
                                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Topic</p>
                                  <p className="mt-1 text-sm font-semibold text-slate-900">Topic #{topic.topicId}</p>
                                </div>
                                <div className="flex items-center gap-3">
                                  <StatusPill label={recommendationLevels[topic.topicId] ?? label} tone={tone} />
                                  <span className="text-sm font-semibold text-slate-900">{topic.score.toFixed(1)}%</span>
                                </div>
                              </div>
                              <div className="mt-4 h-3 rounded-full bg-slate-200 dark:bg-slate-800">
                                <div
                                  className="h-3 rounded-full bg-gradient-to-r from-sky-500 via-cyan-500 to-emerald-500"
                                  style={{ width: `${scoreWidth}%` }}
                                />
                              </div>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </SurfaceCard>

                  <div className="space-y-6">
                    <SurfaceCard
                      title="Priority Follow-Up"
                      description="These are the immediate topics that should influence roadmap generation and review."
                      className="bg-[radial-gradient(circle_at_top_right,_rgba(244,63,94,0.12),_transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.99),rgba(248,250,252,0.96))] dark:bg-[radial-gradient(circle_at_top_right,_rgba(244,63,94,0.12),_transparent_34%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))]"
                    >
                      {weakTopics.length === 0 ? (
                        <p className="text-sm text-emerald-700">No weak topics detected in this diagnostic session.</p>
                      ) : (
                        <ul className="space-y-3">
                          {weakTopics.map((topic) => (
                            <li key={topic.topicId} className="rounded-[24px] border border-rose-200 bg-rose-50/95 px-4 py-4 shadow-[0_16px_40px_-30px_rgba(244,63,94,0.18)] dark:border-rose-500/20 dark:bg-rose-500/10">
                              <p className="text-sm font-semibold text-rose-800">Topic #{topic.topicId}</p>
                              <p className="mt-1 text-sm text-rose-700">{topic.score.toFixed(1)}% mastery</p>
                            </li>
                          ))}
                        </ul>
                      )}
                    </SurfaceCard>

                    <SurfaceCard
                      title="Foundation Gaps"
                      description="These prerequisite topics are holding back progress in downstream weak areas."
                      className="bg-[radial-gradient(circle_at_top_right,_rgba(250,204,21,0.14),_transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.99),rgba(248,250,252,0.96))] dark:bg-[radial-gradient(circle_at_top_right,_rgba(250,204,21,0.12),_transparent_34%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))]"
                    >
                      {foundationGapTopicIds.length === 0 ? (
                        <p className="text-sm text-emerald-700">No prerequisite gaps were detected from the knowledge graph.</p>
                      ) : (
                        <ul className="space-y-3">
                          {foundationGapTopicIds.map((topicId) => (
                            <li key={topicId} className="rounded-[24px] border border-amber-200 bg-amber-50/95 px-4 py-4 shadow-[0_16px_40px_-30px_rgba(245,158,11,0.16)] dark:border-amber-500/20 dark:bg-amber-500/10">
                              <p className="text-sm font-semibold text-amber-900">Topic #{topicId}</p>
                              <p className="mt-1 text-sm text-amber-700">Strengthen this prerequisite before accelerating into dependent roadmap topics.</p>
                            </li>
                          ))}
                        </ul>
                      )}
                    </SurfaceCard>

                    <SurfaceCard
                      title="Strongest Areas"
                      description="Helpful for balancing roadmap intensity and mentor guidance."
                      className="bg-[radial-gradient(circle_at_top_right,_rgba(16,185,129,0.14),_transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.99),rgba(248,250,252,0.96))] dark:bg-[radial-gradient(circle_at_top_right,_rgba(16,185,129,0.12),_transparent_34%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))]"
                    >
                      {strongestTopics.length === 0 ? (
                        <p className="text-sm text-slate-600">No strong topic signals yet.</p>
                      ) : (
                        <ul className="space-y-3">
                          {strongestTopics.map((topic) => (
                            <li key={topic.topicId} className="rounded-[24px] border border-emerald-200 bg-emerald-50/95 px-4 py-4 shadow-[0_16px_40px_-30px_rgba(16,185,129,0.16)] dark:border-emerald-500/20 dark:bg-emerald-500/10">
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
        ) : null}
      </RoleDashboardLayout>
    </RequireRole>
  );
}
