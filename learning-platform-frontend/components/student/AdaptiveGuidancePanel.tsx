"use client";

import Link from "next/link";
import { Brain, Compass, ScanSearch, Sparkles } from "lucide-react";

import Button from "@/components/ui/Button";
import SurfaceCard from "@/components/ui/SurfaceCard";

type AdaptiveGuidancePanelProps = {
  emotionalState: {
    label: string;
    message: string;
    tone: string;
  };
  nextBestAction: {
    title: string;
    description: string;
    ctaLabel: string;
    prompt: string;
  };
  rankedFeatures: Array<{
    key: string;
    title: string;
    reason: string;
  }>;
  focusMode: boolean;
  onToggleFocusMode: () => void;
};

function toneClasses(tone: string): string {
  if (tone === "supportive") {
    return "border-rose-200 bg-rose-50/80 text-rose-950";
  }
  if (tone === "urgent") {
    return "border-amber-200 bg-amber-50/80 text-amber-950";
  }
  if (tone === "celebratory") {
    return "border-emerald-200 bg-emerald-50/80 text-emerald-950";
  }
  return "border-sky-200 bg-sky-50/80 text-sky-950";
}

export default function AdaptiveGuidancePanel({
  emotionalState,
  nextBestAction,
  rankedFeatures,
  focusMode,
  onToggleFocusMode,
}: AdaptiveGuidancePanelProps) {
  return (
    <SurfaceCard
      title="Adaptive guidance"
      description="The interface is reweighting actions, layout, and tone from your recent learning behavior."
      className="mesh-panel"
      actions={
          <Button variant={focusMode ? "primary" : "secondary"} onClick={onToggleFocusMode}>
          <ScanSearch className="h-4 w-4" />
          {focusMode ? "Exit focus mode" : "Enter focus mode"}
        </Button>
      }
    >
      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[28px] border border-white/70 bg-[linear-gradient(135deg,rgba(15,23,42,0.96),rgba(30,41,59,0.92))] p-6 text-white shadow-panel">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/60">Next best action</p>
              <h3 className="mt-3 text-2xl font-semibold tracking-tight">{nextBestAction.title}</h3>
            </div>
            <div className="rounded-[18px] border border-white/10 bg-white/10 p-3">
              <Compass className="h-5 w-5 text-amber-300" />
            </div>
          </div>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-white/75">{nextBestAction.description}</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link
              href={`/mentor/chat?prompt=${encodeURIComponent(nextBestAction.prompt)}`}
              className="inline-flex items-center gap-2 rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-slate-950"
            >
              <Sparkles className="h-4 w-4 text-brand-700" />
              {nextBestAction.ctaLabel}
            </Link>
            <Button variant="ghost" className="bg-white/8 text-white hover:bg-white/12" onClick={onToggleFocusMode}>
              <ScanSearch className="h-4 w-4" />
              {focusMode ? "Keep immersive mode" : "Make this distraction-free"}
            </Button>
          </div>
        </div>

        <div className="space-y-3">
          <div className={`rounded-[24px] border px-4 py-4 ${toneClasses(emotionalState.tone)}`}>
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4" />
              <p className="text-xs font-semibold uppercase tracking-[0.22em]">{emotionalState.label}</p>
            </div>
            <p className="mt-3 text-sm leading-7">{emotionalState.message}</p>
          </div>

          {rankedFeatures.slice(0, 3).map((feature, index) => (
            <div key={feature.key} className="story-card">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                Ranked feature #{index + 1}
              </p>
              <p className="mt-3 text-lg font-semibold text-slate-950">{feature.title}</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">{feature.reason}</p>
            </div>
          ))}
        </div>
      </div>
    </SurfaceCard>
  );
}
