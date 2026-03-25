"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, GripVertical, Sparkles } from "lucide-react";

import Button from "@/components/ui/Button";
import SurfaceCard from "@/components/ui/SurfaceCard";

type InteractiveChallengeLabProps = {
  chapterTitle: string;
  chapterSteps: string[];
};

export default function InteractiveChallengeLab({
  chapterTitle,
  chapterSteps,
}: InteractiveChallengeLabProps) {
  const [items, setItems] = useState(chapterSteps);
  const [completed, setCompleted] = useState(false);

  const targetOrder = useMemo(() => [...chapterSteps].sort((left, right) => left.localeCompare(right)), [chapterSteps]);
  const isSolved = items.every((item, index) => item === targetOrder[index]);

  const moveItem = (index: number, direction: -1 | 1) => {
    const nextIndex = index + direction;
    if (nextIndex < 0 || nextIndex >= items.length) {
      return;
    }
    const next = [...items];
    [next[index], next[nextIndex]] = [next[nextIndex], next[index]];
    setItems(next);
  };

  return (
    <SurfaceCard
      title="Challenge lab"
      description="A lightweight interactive mission that turns a chapter into a manipulable sequence."
      className="mesh-panel"
      actions={
        <Button
          variant={isSolved ? "primary" : "secondary"}
          onClick={() => setCompleted(isSolved)}
          disabled={!isSolved}
        >
          <CheckCircle2 className="h-4 w-4" />
          Claim completion
        </Button>
      }
    >
      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="story-card">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Mini simulation</p>
          <p className="mt-3 text-2xl font-semibold text-slate-950">{chapterTitle}</p>
          <p className="mt-3 text-sm leading-7 text-slate-600">
            Reorder this chapter into a clean progression path. It is a compact “game-like” interaction that makes the roadmap feel participatory instead of passive.
          </p>
          <div className="mt-5 inline-flex items-center gap-2 rounded-full bg-slate-950 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-white">
            <Sparkles className="h-3.5 w-3.5 text-amber-300" />
            Mission objective
          </div>
        </div>

        <div className="space-y-3">
          {items.map((item, index) => (
            <motion.div
              layout
              key={`${item}-${index}`}
              className="flex items-center justify-between gap-4 rounded-[24px] border border-white/70 bg-white/80 px-4 py-3 shadow-sm"
            >
              <div className="flex items-center gap-3">
                <div className="rounded-[16px] bg-slate-100 p-2 text-slate-500">
                  <GripVertical className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-950">{item}</p>
                  <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-400">Step {index + 1}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" onClick={() => moveItem(index, -1)}>Up</Button>
                <Button variant="ghost" onClick={() => moveItem(index, 1)}>Down</Button>
              </div>
            </motion.div>
          ))}

          <AnimatePresence>
            {completed ? (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="rounded-[24px] border border-emerald-200 bg-emerald-50/85 px-4 py-4"
              >
                <div className="flex items-center gap-2 text-emerald-800">
                  <CheckCircle2 className="h-5 w-5" />
                  <p className="text-sm font-semibold uppercase tracking-[0.18em]">Mission complete</p>
                </div>
                <p className="mt-2 text-sm leading-6 text-emerald-900/80">
                  The chapter sequence is now aligned. This is where a production version could award XP, unlock a badge, or advance the next quest.
                </p>
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>
      </div>
    </SurfaceCard>
  );
}
