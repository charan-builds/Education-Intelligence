"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Play, Sparkles, Wand2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import Button from "@/components/ui/Button";

type DemoModeShowcaseProps = {
  steps: Array<{
    title: string;
    description: string;
    accent: string;
  }>;
};

export default function DemoModeShowcase({ steps }: DemoModeShowcaseProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  useEffect(() => {
    if (!isPlaying || steps.length <= 1) {
      return undefined;
    }

    const timer = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % steps.length);
    }, 3200);

    return () => window.clearInterval(timer);
  }, [isPlaying, steps.length]);

  const activeStep = useMemo(() => steps[activeIndex] ?? steps[0], [activeIndex, steps]);

  if (!activeStep) {
    return null;
  }

  return (
    <div className="story-card premium-hero min-h-[240px] p-6 md:p-7">
      <div className="premium-orb left-0 top-0 h-24 w-24 bg-teal-300/35" />
      <div className="premium-orb bottom-4 right-0 h-28 w-28 bg-orange-300/30" style={{ animationDelay: "1.2s" }} />
      <div className="relative flex h-full flex-col justify-between gap-6">
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/70 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.26em] text-slate-700">
            <Wand2 className="h-3.5 w-3.5 text-brand-700" />
            Demo Mode
          </span>
          <span className="inline-flex items-center gap-2 rounded-full bg-slate-950 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-white">
            <Sparkles className="h-3.5 w-3.5 text-amber-300" />
            Auto walkthrough
          </span>
        </div>

        <div>
          <AnimatePresence mode="wait">
            <motion.div
              key={activeStep.title}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -14 }}
              transition={{ duration: 0.45, ease: "easeOut" }}
            >
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">{activeStep.accent}</p>
              <h3 className="mt-3 max-w-xl text-3xl font-semibold tracking-tight text-slate-950">{activeStep.title}</h3>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">{activeStep.description}</p>
            </motion.div>
          </AnimatePresence>
        </div>

        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-wrap gap-2">
            {steps.map((step, index) => (
              <button
                key={step.title}
                type="button"
                onClick={() => setActiveIndex(index)}
                className={[
                  "h-2.5 rounded-full transition-all duration-300",
                  index === activeIndex ? "w-10 bg-slate-950" : "w-2.5 bg-slate-400/50 hover:bg-slate-500/60",
                ].join(" ")}
                aria-label={`Show demo step ${index + 1}`}
              />
            ))}
          </div>

          <Button variant={isPlaying ? "secondary" : "primary"} onClick={() => setIsPlaying((current) => !current)}>
            <Play className="h-4 w-4" />
            {isPlaying ? "Pause tour" : "Play tour"}
          </Button>
        </div>
      </div>
    </div>
  );
}
