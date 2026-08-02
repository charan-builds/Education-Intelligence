"use client";

import Link from "next/link";
import { motion } from "framer-motion";

import type { DiagnosticResult } from "@/types/diagnostic";
import type { TopicSummary } from "@/types/topic";
import RoadmapViewer from "@/components/diagnostic/RoadmapViewer";
import { getLearnerRoutes } from "@/utils/appRoutes";

type Props = {
  result: DiagnosticResult;
  topics: TopicSummary[];
  role: string | null | undefined;
};

function classifyScore(score: number) {
  if (score < 50) {
    return "Weak";
  }
  if (score <= 70) {
    return "Moderate";
  }
  return "Strong";
}

export default function ResultDashboard({ result, topics, role }: Props) {
  const learnerRoutes = getLearnerRoutes(role);
  const topicNameMap = new Map(topics.map((topic) => [topic.id, topic.name]));
  const topicRows = Object.entries(result.topic_scores)
    .map(([topicId, score]) => ({
      topicId: Number(topicId),
      score: Number(score),
      name: topicNameMap.get(Number(topicId)) ?? `Topic ${topicId}`,
    }))
    .sort((a, b) => a.score - b.score);
  const overallScore = topicRows.length
    ? Math.round(topicRows.reduce((sum, item) => sum + item.score, 0) / topicRows.length)
    : 0;
  const weakAreas = topicRows.filter((item) => item.score < 50);
  const strengthAreas = topicRows.filter((item) => item.score > 70);

  return (
    <div className="diagnostic-shell min-h-screen text-slate-100">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <motion.section
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="diagnostic-glass p-6 sm:p-8"
        >
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-violet-300">Post-test analysis</p>
              <h1 className="mt-3 text-4xl font-semibold text-slate-50">Diagnostic complete</h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">
                Your roadmap is now shaped around weak foundations first, then Python, data cleaning, libraries, and machine learning progression.
              </p>
            </div>
            <div className="rounded-[28px] bg-violet-600 px-6 py-5 text-center shadow-lg shadow-violet-900/40">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-violet-100">Overall Score</p>
              <p className="mt-2 text-5xl font-semibold text-white">{overallScore}%</p>
            </div>
          </div>
        </motion.section>

        <section className="grid gap-4 md:grid-cols-3">
          <div className="diagnostic-glass-soft p-5">
            <p className="text-sm text-slate-400">Topic-wise performance</p>
            <p className="mt-2 text-3xl font-semibold text-slate-50">{topicRows.length}</p>
          </div>
          <div className="diagnostic-glass-soft p-5">
            <p className="text-sm text-slate-400">Weak areas</p>
            <p className="mt-2 text-3xl font-semibold text-rose-300">{weakAreas.length}</p>
          </div>
          <div className="diagnostic-glass-soft p-5">
            <p className="text-sm text-slate-400">Strength areas</p>
            <p className="mt-2 text-3xl font-semibold text-emerald-300">{strengthAreas.length}</p>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="diagnostic-glass p-6">
            <p className="text-sm font-medium text-violet-300">Topic-wise Performance</p>
            <div className="mt-5 space-y-3">
              {topicRows.map((item) => (
                <div key={item.topicId} className="rounded-[24px] border border-slate-800 bg-slate-900/70 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-100">{item.name}</p>
                      <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500">{classifyScore(item.score)}</p>
                    </div>
                    <span className="text-lg font-semibold text-slate-50">{Math.round(item.score)}%</span>
                  </div>
                  <div className="mt-3 h-2 rounded-full bg-slate-800">
                    <div
                      className={[
                        "h-2 rounded-full",
                        item.score < 50 ? "bg-rose-500" : item.score <= 70 ? "bg-amber-500" : "bg-emerald-500",
                      ].join(" ")}
                      style={{ width: `${Math.max(8, Math.min(100, item.score))}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            <div className="diagnostic-glass-soft p-6">
              <p className="text-sm font-medium text-violet-300">Weak Areas</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {weakAreas.length > 0 ? weakAreas.map((item) => (
                  <span key={item.topicId} className="rounded-full bg-rose-500/15 px-3 py-1 text-sm font-medium text-rose-200">
                    {item.name}
                  </span>
                )) : <p className="text-sm text-slate-400">No weak areas detected.</p>}
              </div>
            </div>

            <div className="diagnostic-glass-soft p-6">
              <p className="text-sm font-medium text-violet-300">Strength Areas</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {strengthAreas.length > 0 ? strengthAreas.map((item) => (
                  <span key={item.topicId} className="rounded-full bg-emerald-500/15 px-3 py-1 text-sm font-medium text-emerald-200">
                    {item.name}
                  </span>
                )) : <p className="text-sm text-slate-400">No strong areas detected yet.</p>}
              </div>
            </div>

            <div className="diagnostic-glass-soft p-6">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-violet-300">Generated Roadmap</p>
                  <p className="mt-2 text-sm leading-7 text-slate-400">
                    Weak topics are prioritized before downstream AI/ML modules.
                  </p>
                </div>
                <Link href={learnerRoutes.roadmap} className="diagnostic-button-primary rounded-2xl px-4 py-2 text-sm font-semibold text-white">
                  Open Roadmap
                </Link>
              </div>
              <div className="mt-5">
                <RoadmapViewer roadmap={result.roadmap} weakTopicNames={weakAreas.map((item) => item.name)} role={role} />
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
