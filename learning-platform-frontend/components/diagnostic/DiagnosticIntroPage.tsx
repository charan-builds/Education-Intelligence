"use client";

import { motion } from "framer-motion";

import { DIAGNOSTIC_SECTIONS, DIAGNOSTIC_TRACK_NAME, STRICT_FLOW_STEPS } from "@/features/diagnostic/config";

type Props = {
  selectedGoalName: string | null;
  selectedPath: string | null;
  onSelectPath: () => void;
  onStart: () => void;
  isStarting?: boolean;
};

export default function DiagnosticIntroPage({
  selectedGoalName,
  selectedPath,
  onSelectPath,
  onStart,
  isStarting = false,
}: Props) {
  return (
    <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
      <motion.section
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="diagnostic-glass p-6 sm:p-8"
      >
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-violet-300">Step 2 and 3</p>
          <h2 className="text-3xl font-semibold text-slate-50">Lock the diagnostic path</h2>
          <p className="text-sm leading-7 text-slate-400">
            The diagnostic is strict by design. The learner must confirm the goal, lock the Python track, then enter fullscreen before the first question.
          </p>
        </div>

        <div className="mt-6 space-y-4">
          <div className="rounded-[28px] border border-violet-400/30 bg-violet-500/10 p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-violet-200">Selected Goal</p>
            <h3 className="mt-2 text-2xl font-semibold text-slate-50">{selectedGoalName ?? "No goal selected"}</h3>
            <p className="mt-2 text-sm text-slate-300">Recommended learning target: AI/ML Engineer</p>
          </div>

          <button
            type="button"
            onClick={onSelectPath}
            className={[
              "w-full rounded-[28px] border p-6 text-left transition",
              selectedPath
                ? "border-violet-400/70 bg-violet-500/12"
                : "border-slate-700/70 bg-slate-900/55 hover:border-slate-500/80 hover:bg-slate-900/80",
            ].join(" ")}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Learning Path</p>
                <h3 className="mt-2 text-2xl font-semibold text-slate-50">{DIAGNOSTIC_TRACK_NAME}</h3>
                <p className="mt-2 text-sm leading-7 text-slate-400">
                  Python fundamentals, data cleaning flow, core libraries, and machine learning readiness.
                </p>
              </div>
              <span className="rounded-full bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-300">
                {selectedPath ? "Locked" : "Required"}
              </span>
            </div>
          </button>
        </div>

        <div className="mt-6 rounded-[28px] border border-amber-400/20 bg-amber-500/10 p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-200">Strict rules</p>
          <ul className="mt-3 space-y-2 text-sm text-slate-200">
            <li>Fullscreen is mandatory.</li>
            <li>Tab switching more than 2 times triggers auto-submit.</li>
            <li>Copy, paste, right click, and refresh shortcuts are blocked.</li>
            <li>Timer cannot be paused and auto-submits on expiry.</li>
          </ul>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={onStart}
            disabled={!selectedGoalName || !selectedPath || isStarting}
            className="diagnostic-button-primary inline-flex items-center justify-center rounded-2xl px-5 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isStarting ? "Starting..." : "Start Diagnostic"}
          </button>
        </div>
      </motion.section>

      <motion.section
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: "easeOut", delay: 0.05 }}
        className="diagnostic-glass-soft p-6 sm:p-8"
      >
        <div className="space-y-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-violet-300">Diagnostic blueprint</p>
            <h2 className="mt-2 text-3xl font-semibold text-slate-50">What this test measures</h2>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {STRICT_FLOW_STEPS.map((step, index) => (
              <div key={step} className="rounded-2xl border border-slate-800 bg-slate-900/70 px-4 py-3 text-sm text-slate-200">
                <span className="mr-2 text-violet-300">0{index + 1}</span>
                {step}
              </div>
            ))}
          </div>

          <div className="space-y-3">
            {DIAGNOSTIC_SECTIONS.map((section) => (
              <div key={section.level} className="rounded-[26px] border border-slate-800 bg-slate-900/70 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.24em] text-violet-300">{section.level}</p>
                    <h3 className="mt-1 text-lg font-semibold text-slate-50">{section.title}</h3>
                  </div>
                  <span className="rounded-full bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-300">
                    {section.topics.length} topics
                  </span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {section.topics.map((topic) => (
                    <span key={topic} className="rounded-full bg-slate-800 px-3 py-1 text-xs font-medium text-slate-300">
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </motion.section>
    </div>
  );
}
