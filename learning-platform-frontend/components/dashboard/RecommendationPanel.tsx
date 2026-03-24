"use client";

import { Lightbulb } from "lucide-react";
import React from "react";

import SurfaceCard from "@/components/ui/SurfaceCard";

type RecommendationPanelProps = {
  title?: string;
  description?: string;
  items: string[];
};

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
            key={`${item}-${index}`}
            className="flex gap-3 rounded-[24px] border border-indigo-100 bg-[linear-gradient(135deg,rgba(238,242,255,0.95),rgba(224,231,255,0.72))] px-4 py-3 dark:border-indigo-500/20 dark:bg-indigo-500/10"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-[18px] bg-white/90 text-brand-700 shadow-sm dark:bg-slate-900/80 dark:text-brand-200">
              <Lightbulb className="h-4 w-4" />
            </div>
            <p className="text-sm leading-7 text-slate-700 dark:text-slate-200">{item}</p>
          </div>
        ))}
      </div>
    </SurfaceCard>
  );
}
