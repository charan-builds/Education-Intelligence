import React from "react";

type StatusPillProps = {
  label: string;
  tone?: "default" | "success" | "warning" | "danger";
};

export default function StatusPill({ label, tone = "default" }: StatusPillProps) {
  const toneMap = {
    default: "border-slate-200 bg-slate-50/95 text-slate-700 dark:border-slate-700/60 dark:bg-slate-900/60 dark:text-slate-200",
    success: "border-emerald-200 bg-emerald-50/95 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/15 dark:text-emerald-200",
    warning: "border-amber-200 bg-amber-50/95 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/15 dark:text-amber-200",
    danger: "border-rose-200 bg-rose-50/95 text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/15 dark:text-rose-200",
  } as const;

  return (
    <span className={`rounded-full border px-3 py-1.5 text-xs font-semibold capitalize backdrop-blur transition duration-200 ${toneMap[tone]}`}>
      {label.replaceAll("_", " ")}
    </span>
  );
}
