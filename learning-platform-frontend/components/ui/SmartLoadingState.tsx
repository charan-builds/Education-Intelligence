"use client";

import { motion } from "framer-motion";
import { BrainCircuit, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const loadingQuotes = [
  "Learning never exhausts the mind.",
  "Tiny daily progress compounds faster than motivation.",
  "Mastery is built in layers, not leaps.",
  "Strong fundamentals make advanced work feel effortless.",
];

const loadingFacts = [
  "Did you know? Active recall is usually more effective than passive rereading.",
  "Did you know? Spaced repetition improves long-term retention.",
  "Did you know? Teaching a concept is one of the fastest ways to test understanding.",
  "Did you know? Short focused sessions often outperform marathon study blocks.",
];

type SmartLoadingStateProps = {
  title?: string;
  description?: string;
  compact?: boolean;
};

export default function SmartLoadingState({
  title = "Preparing your learning intelligence",
  description = "We are gathering signals, shaping insights, and warming up the mentor experience.",
  compact = false,
}: SmartLoadingStateProps) {
  const [quoteIndex, setQuoteIndex] = useState(0);
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const quoteTimer = window.setInterval(() => {
      setQuoteIndex((current) => (current + 1) % loadingQuotes.length);
    }, 2600);
    const secondTimer = window.setInterval(() => {
      setSeconds((current) => current + 1);
    }, 1000);
    return () => {
      window.clearInterval(quoteTimer);
      window.clearInterval(secondTimer);
    };
  }, []);

  const estimate = useMemo(() => Math.max(4, 12 - Math.min(seconds, 8)), [seconds]);
  const progress = useMemo(() => Math.min(92, 22 + seconds * 9), [seconds]);

  return (
    <div className="glass-surface soft-ring relative overflow-hidden rounded-[32px] border border-white/60 p-6 dark:border-violet-500/20">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(139,92,246,0.20),transparent_24%),radial-gradient(circle_at_bottom_left,rgba(192,132,252,0.16),transparent_22%)]" />
      <div className="relative space-y-5">
        <div className="flex items-center gap-3">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 5.5, ease: "linear" }}
            className="flex h-12 w-12 items-center justify-center rounded-[18px] bg-[linear-gradient(135deg,#6C5CE7,#8B5CF6)] text-white shadow-lg shadow-violet-400/30 dark:bg-[linear-gradient(135deg,#7C6CF2,#A78BFA)] dark:text-white"
          >
            <BrainCircuit className="h-5 w-5" />
          </motion.div>
          <div>
            <h2 className="text-xl font-semibold text-violet-950 dark:text-violet-50">{title}</h2>
            {!compact ? <p className="mt-1 text-sm text-violet-800/78 dark:text-violet-100/74">{description}</p> : null}
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-[0.26em] text-violet-500 dark:text-violet-200/70">
            <span>Estimated wait</span>
            <span>{estimate}s</span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-violet-100 dark:bg-violet-950/80">
            <motion.div
              className="h-full rounded-full bg-[linear-gradient(90deg,#6C5CE7,#8B5CF6,#C084FC)]"
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            />
          </div>
        </div>

        <div className={compact ? "grid gap-3" : "grid gap-4 md:grid-cols-2"}>
          <motion.div
            key={`quote-${quoteIndex}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="rounded-[24px] border border-white/60 bg-white/70 p-4 dark:border-violet-500/20 dark:bg-violet-950/50"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-violet-700 dark:text-violet-200">Now loading</p>
            <p className="mt-3 text-base leading-7 text-violet-900 dark:text-violet-50">
              &ldquo;{loadingQuotes[quoteIndex]}&rdquo;
            </p>
          </motion.div>
          <div className="rounded-[24px] border border-white/60 bg-white/70 p-4 dark:border-violet-500/20 dark:bg-violet-950/50">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.24em] text-fuchsia-600 dark:text-fuchsia-200">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Did you know?</span>
            </div>
            <p className="mt-3 text-sm leading-7 text-violet-800/80 dark:text-violet-100/74">
              {loadingFacts[quoteIndex]}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
