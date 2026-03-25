"use client";

import { motion } from "framer-motion";
import { BookOpenText, CheckCircle2, Clock3, Sparkles, Target } from "lucide-react";

import SurfaceCard from "@/components/ui/SurfaceCard";

type ProgressStoryTimelineProps = {
  items: Array<{
    title: string;
    description: string;
    tone: "complete" | "active" | "upcoming";
  }>;
};

const toneStyles = {
  complete: {
    icon: CheckCircle2,
    color: "bg-emerald-500 text-white",
    line: "from-emerald-400/80 to-emerald-200/20",
  },
  active: {
    icon: Sparkles,
    color: "bg-brand-700 text-white",
    line: "from-brand-500/80 to-cyan-200/20",
  },
  upcoming: {
    icon: Clock3,
    color: "bg-amber-400 text-slate-950",
    line: "from-amber-300/80 to-orange-100/20",
  },
} as const;

export default function ProgressStoryTimeline({ items }: ProgressStoryTimelineProps) {
  return (
    <SurfaceCard
      title="Learning journey timeline"
      description="A story view of what you have mastered, where momentum is peaking, and what unlocks next."
      actions={
        <div className="inline-flex items-center gap-2 rounded-full bg-slate-950 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-white">
          <Target className="h-3.5 w-3.5 text-amber-300" />
          Storytelling dashboard
        </div>
      }
    >
      <div className="mb-5 rounded-[24px] border border-white/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.92),rgba(255,247,237,0.76))] px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="rounded-[16px] bg-slate-950 p-2 text-white">
            <BookOpenText className="h-4 w-4 text-amber-300" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Story mode</p>
            <p className="mt-1 text-sm leading-6 text-slate-700">Every milestone is framed like a chapter beat so progress feels legible, cumulative, and rewarding.</p>
          </div>
        </div>
      </div>
      <div className="space-y-4">
        {items.map((item, index) => {
          const tone = toneStyles[item.tone];
          const Icon = tone.icon;

          return (
            <motion.div
              key={`${item.title}-${index}`}
              initial={{ opacity: 0, x: -18 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.35, delay: index * 0.06 }}
              className="grid grid-cols-[52px_1fr] gap-4"
            >
              <div className="flex flex-col items-center">
                <div className={`flex h-12 w-12 items-center justify-center rounded-2xl ${tone.color}`}>
                  <Icon className="h-5 w-5" />
                </div>
                {index < items.length - 1 ? <div className={`mt-3 h-full w-px bg-gradient-to-b ${tone.line}`} /> : null}
              </div>
              <div className="story-card">
                <p className="text-sm font-semibold text-slate-950">{item.title}</p>
                <p className="mt-2 text-sm leading-7 text-slate-600">{item.description}</p>
              </div>
            </motion.div>
          );
        })}
      </div>
    </SurfaceCard>
  );
}
