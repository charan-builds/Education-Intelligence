"use client";

import { motion } from "framer-motion";

import type { Goal } from "@/types/goal";

type Props = {
  goals: Goal[];
  selectedGoalId: number | null;
  onSelectGoal: (goal: Goal) => void;
  onContinue: () => void;
  isBusy?: boolean;
};

export default function GoalSelectionPage({ goals, selectedGoalId, onSelectGoal, onContinue, isBusy = false }: Props) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="diagnostic-glass p-6 sm:p-8"
    >
      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-violet-300">Step 1</p>
        <h2 className="text-3xl font-semibold text-slate-50">Select your goal</h2>
        <p className="max-w-3xl text-sm leading-7 text-slate-400">
          Choose the target role first. The diagnostic is locked to a strict sequence and cannot be skipped once started.
        </p>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        {goals.map((goal) => {
          const isSelected = goal.id === selectedGoalId;
          return (
            <button
              key={goal.id}
              type="button"
              onClick={() => onSelectGoal(goal)}
              className={[
                "rounded-[28px] border p-6 text-left transition duration-200",
                isSelected
                  ? "border-violet-400/70 bg-violet-500/12 shadow-[0_24px_70px_-34px_rgba(124,58,237,0.7)]"
                  : "border-slate-700/70 bg-slate-900/55 hover:border-slate-500/80 hover:bg-slate-900/80",
              ].join(" ")}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-xl font-semibold text-slate-50">{goal.name}</h3>
                  {goal.is_recommended ? (
                    <span className="rounded-full bg-violet-500/15 px-3 py-1 text-xs font-semibold text-violet-200 ring-1 ring-violet-400/30">
                      Recommended
                    </span>
                  ) : null}
                </div>
                <p className="text-sm leading-7 text-slate-400">{goal.description}</p>
                <div className="flex flex-wrap gap-2">
                  {(goal.skills_covered ?? []).slice(0, 4).map((skill) => (
                    <span key={skill} className="rounded-full bg-slate-800 px-3 py-1 text-xs font-medium text-slate-300">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      <div className="mt-6 flex justify-end">
        <button
          type="button"
          onClick={onContinue}
          disabled={!selectedGoalId || isBusy}
          className="diagnostic-button-primary inline-flex items-center justify-center rounded-2xl px-5 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50"
        >
          Continue
        </button>
      </div>
    </motion.section>
  );
}
