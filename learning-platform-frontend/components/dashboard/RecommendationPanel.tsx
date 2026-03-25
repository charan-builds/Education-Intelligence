"use client";

import { ArrowRight, Lightbulb, Sparkles, Target } from "lucide-react";
import React from "react";
import Link from "next/link";

import SurfaceCard from "@/components/ui/SurfaceCard";
import StatusPill from "@/components/ui/StatusPill";

type RecommendationPanelProps = {
  title?: string;
  description?: string;
  items: Array<{
    title: string;
    message: string;
    why?: string;
    confidenceLabel?: string;
    href?: string;
    ctaLabel?: string;
    tone?: string;
  }>;
};

function normalizeTone(tone?: string): "default" | "success" | "warning" | "danger" {
  if (tone === "success") {
    return "success";
  }
  if (tone === "warning") {
    return "warning";
  }
  if (tone === "danger") {
    return "danger";
  }
  return "default";
}

export default function RecommendationPanel({
  title = "Recommended next moves",
  description = "Actionable guidance assembled from the current backend signals.",
  items,
}: RecommendationPanelProps) {
  return (
    <SurfaceCard title={title} description={description}>
      <div className="space-y-3">
        {items.map((item, index) => (
          <div
            key={`${item.title}-${index}`}
            className="rounded-[24px] border border-indigo-100 bg-[linear-gradient(135deg,rgba(238,242,255,0.95),rgba(224,231,255,0.72))] px-4 py-4 dark:border-indigo-500/20 dark:bg-indigo-500/10"
          >
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-[18px] bg-white/90 text-brand-700 shadow-sm dark:bg-slate-900/80 dark:text-brand-200">
                <Lightbulb className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{item.title}</p>
                  {item.confidenceLabel ? <StatusPill label={item.confidenceLabel} tone={normalizeTone(item.tone)} /> : null}
                </div>
                <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-200">{item.message}</p>
                {item.why ? (
                  <div className="mt-3 rounded-2xl border border-white/70 bg-white/70 px-3 py-2 dark:border-slate-700 dark:bg-slate-950/40">
                    <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                      <Sparkles className="h-3.5 w-3.5" />
                      Why this now
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.why}</p>
                  </div>
                ) : null}
                {item.href ? (
                  <Link
                    href={item.href}
                    className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-slate-900 transition hover:translate-x-0.5 dark:text-slate-100"
                  >
                    <Target className="h-4 w-4 text-brand-600" />
                    {item.ctaLabel ?? "Take action"}
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                ) : null}
              </div>
            </div>
          </div>
        ))}
      </div>
    </SurfaceCard>
  );
}
