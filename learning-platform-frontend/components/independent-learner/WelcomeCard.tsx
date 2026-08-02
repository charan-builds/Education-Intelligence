"use client";

import Link from "next/link";
import { Sparkles } from "lucide-react";

import SurfaceCard from "@/components/ui/SurfaceCard";

type WelcomeCardProps = {
  name: string;
  quote: string;
  continueHref: string;
  continueLabel: string;
  completionPercent: number;
};

export default function WelcomeCard({
  name,
  quote,
  continueHref,
  continueLabel,
  completionPercent,
}: WelcomeCardProps) {
  return (
    <SurfaceCard
      title={`Welcome, ${name}`}
      description="This personal onboarding flow turns your independent learner workspace into a real study system before diagnostics and roadmap generation begin."
      className="border-violet-200 bg-[radial-gradient(circle_at_top_left,_rgba(168,85,247,0.18),_transparent_38%),linear-gradient(180deg,rgba(255,255,255,0.98),rgba(245,243,255,0.96))] dark:border-violet-700 dark:bg-[radial-gradient(circle_at_top_left,_rgba(168,85,247,0.22),_transparent_38%),linear-gradient(180deg,rgba(46,16,101,0.38),rgba(15,23,42,0.96))]"
    >
      <div className="space-y-6">
        <div className="rounded-[28px] border border-violet-200 bg-white/80 p-6 shadow-[0_22px_60px_-36px_rgba(139,92,246,0.45)] dark:border-violet-700 dark:bg-violet-950/50">
          <div className="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-violet-700 dark:border-violet-700 dark:bg-violet-900/40 dark:text-violet-200">
            <Sparkles className="h-4 w-4" />
            Daily Momentum
          </div>
          <div className="mt-5">
            <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-[0.18em] text-violet-500">
              <span>Profile Completion</span>
              <span>{completionPercent}%</span>
            </div>
            <div className="mt-3 h-3 overflow-hidden rounded-full bg-violet-100 dark:bg-violet-900/50">
              <div
                className="h-full rounded-full bg-gradient-to-r from-violet-500 via-fuchsia-500 to-purple-500 transition-[width] duration-500"
                style={{ width: `${completionPercent}%` }}
              />
            </div>
          </div>
          <p className="mt-4 text-lg font-semibold leading-8 text-slate-950 dark:text-slate-50">{quote}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link
            href={continueHref}
            className="inline-flex items-center rounded-2xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-violet-500"
          >
            {continueLabel}
          </Link>
        </div>
      </div>
    </SurfaceCard>
  );
}
