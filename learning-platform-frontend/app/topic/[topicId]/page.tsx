"use client";

export const dynamic = "force-dynamic";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { getTopic } from "@/services/topicService";

function difficultyLabel(level: number): string {
  if (level <= 1) {
    return "easy";
  }
  if (level === 2) {
    return "medium";
  }
  return "hard";
}

export default function TopicLearningPage() {
  const params = useParams<{ topicId: string }>();
  const topicId = Number(params.topicId);

  const topicQuery = useQuery({
    queryKey: ["topic", topicId],
    queryFn: () => getTopic(topicId),
    enabled: Number.isFinite(topicId) && topicId > 0,
  });

  if (!Number.isFinite(topicId) || topicId <= 0) {
    return (
      <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
        <h1 className="text-3xl font-semibold tracking-tight">Topic Learning</h1>
        <p className="mt-3 text-slate-600">Invalid topic id.</p>
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Topic Learning</h1>
          <p className="mt-2 text-slate-600">Topic #{topicId}</p>
        </div>
        <Link href="/roadmap/view" className="rounded-lg bg-brand-600 px-4 py-2 text-white hover:bg-brand-700">
          Back to Roadmap
        </Link>
      </div>

      {topicQuery.isLoading && <p className="mt-8 text-slate-600">Loading topic...</p>}
      {topicQuery.isError && <p className="mt-8 text-red-600">Failed to load topic data.</p>}

      {topicQuery.data && (
        <div className="mt-8 space-y-6">
          <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">{topicQuery.data.name}</h2>
            <p className="mt-3 text-slate-700">{topicQuery.data.description}</p>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900">Examples</h3>
            {topicQuery.data.examples.length === 0 ? (
              <p className="mt-3 text-slate-600">No examples available.</p>
            ) : (
              <ul className="mt-3 list-disc space-y-2 pl-5 text-slate-700">
                {topicQuery.data.examples.map((example, index) => (
                  <li key={`${index}-${example}`}>{example}</li>
                ))}
              </ul>
            )}
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900">Practice Questions</h3>
            {topicQuery.data.practice_questions.length === 0 ? (
              <p className="mt-3 text-slate-600">No practice questions available.</p>
            ) : (
              <ul className="mt-4 space-y-3">
                {topicQuery.data.practice_questions.map((question) => (
                  <li key={question.id} className="rounded-lg border border-slate-200 px-4 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-medium text-slate-900">Q#{question.id}</p>
                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs capitalize text-slate-700">
                        {difficultyLabel(question.difficulty)}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-700">{question.question_text}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </main>
  );
}
