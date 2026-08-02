"use client";

import Link from "next/link";

import type { Roadmap } from "@/types/roadmap";
import { DIAGNOSTIC_SECTIONS } from "@/features/diagnostic/config";
import { getLearnerTopicPath } from "@/utils/appRoutes";

type Props = {
  roadmap: Roadmap | null;
  weakTopicNames: string[];
  role: string | null | undefined;
};

export default function RoadmapViewer({ roadmap, weakTopicNames, role }: Props) {
  if (roadmap?.steps?.length) {
    return (
      <div className="space-y-3">
        {roadmap.steps.slice(0, 6).sort((a, b) => a.priority - b.priority).map((step) => (
          <Link
            key={step.id}
            href={getLearnerTopicPath(role, step.topic_id)}
            className="flex flex-col gap-3 rounded-[24px] border border-slate-800 bg-slate-900/70 p-4 transition hover:border-violet-400/40 hover:bg-slate-900"
          >
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-slate-100">Step {step.priority}</p>
              <span className="rounded-full bg-violet-500/15 px-3 py-1 text-xs font-semibold text-violet-200 ring-1 ring-violet-400/30">
                {step.difficulty}
              </span>
            </div>
            <p className="text-sm text-slate-300">Topic #{step.topic_id}</p>
            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{step.progress_status.replaceAll("_", " ")}</p>
          </Link>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {DIAGNOSTIC_SECTIONS.map((section) => (
        <div key={section.level} className="rounded-[24px] border border-slate-800 bg-slate-900/70 p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-violet-300">{section.level}</p>
              <h3 className="mt-1 text-lg font-semibold text-slate-50">{section.title}</h3>
            </div>
            <span className="rounded-full bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-300">
              ordered
            </span>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {section.topics.map((topic) => {
              const isWeak = weakTopicNames.includes(topic);
              return (
                <span
                  key={topic}
                  className={[
                    "rounded-full px-3 py-1 text-xs font-medium",
                    isWeak ? "bg-rose-500/15 text-rose-200" : "bg-slate-800 text-slate-300",
                  ].join(" ")}
                >
                  {topic}
                </span>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

