"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { getMentorProgressAnalysis } from "@/services/mentorInsightsService";

export default function MentorProgressAnalysis() {
  const query = useQuery({
    queryKey: ["mentor-progress-analysis"],
    queryFn: () => getMentorProgressAnalysis(),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });

  const topTopicImprovements = useMemo(() => {
    const entries = Object.entries(query.data?.topic_improvements ?? {})
      .map(([topicId, gap]) => ({ topicId: Number(topicId), gap: Number(gap) }))
      .sort((a, b) => b.gap - a.gap)
      .slice(0, 5);
    return entries;
  }, [query.data?.topic_improvements]);

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Progress Analysis</h2>

      {query.isLoading && <p className="mt-3 text-sm text-slate-600">Loading analysis...</p>}
      {query.isError && <p className="mt-3 text-sm text-red-600">Failed to load progress analysis.</p>}

      {!query.isLoading && !query.isError && (
        <div className="mt-3 space-y-4">
          <div>
            <p className="text-sm font-medium text-slate-800">Topic Improvements</p>
            {topTopicImprovements.length === 0 ? (
              <p className="mt-1 text-sm text-slate-600">No topic improvement gaps detected.</p>
            ) : (
              <ul className="mt-1 space-y-1 text-sm text-slate-700">
                {topTopicImprovements.map((item) => (
                  <li key={item.topicId}>Topic #{item.topicId}: {item.gap.toFixed(1)} improvement points</li>
                ))}
              </ul>
            )}
          </div>

          <div>
            <p className="text-sm font-medium text-slate-800">Weekly Progress</p>
            <ul className="mt-1 space-y-1 text-sm text-slate-700">
              {(query.data?.weekly_progress ?? []).map((item) => (
                <li key={item.week}>{item.week}: {item.completion_percent.toFixed(1)}%</li>
              ))}
            </ul>
          </div>

          <div>
            <p className="text-sm font-medium text-slate-800">Recommended Focus</p>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-700">
              {(query.data?.recommended_focus ?? []).map((item, idx) => (
                <li key={`${idx}-${item}`}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </section>
  );
}
