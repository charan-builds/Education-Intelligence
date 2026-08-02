"use client";

import { motion } from "framer-motion";

type Props = {
  remainingSeconds: number;
};

function formatTime(remainingSeconds: number) {
  const minutes = Math.floor(remainingSeconds / 60);
  const seconds = remainingSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export default function TimerComponent({ remainingSeconds }: Props) {
  const isCritical = remainingSeconds <= 30;

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={[
        "inline-flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm font-semibold shadow-lg",
        isCritical
          ? "timer-critical border-rose-400/40 bg-rose-500/10 text-rose-200"
          : "border-violet-400/30 bg-slate-900/70 text-slate-100",
      ].join(" ")}
    >
      <span className="text-xs uppercase tracking-[0.2em] text-slate-400">Time Left</span>
      <span className={isCritical ? "text-rose-200" : "text-violet-200"}>{formatTime(remainingSeconds)}</span>
    </motion.div>
  );
}
