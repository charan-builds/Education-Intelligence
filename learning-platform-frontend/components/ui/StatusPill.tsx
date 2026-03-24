import React from "react";

type StatusPillProps = {
  label: string;
  tone?: "default" | "success" | "warning" | "danger";
};

export default function StatusPill({ label, tone = "default" }: StatusPillProps) {
  const toneMap = {
    default: "border-slate-200 bg-white/80 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200",
    success: "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-200",
    warning: "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200",
    danger: "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-200",
  } as const;

  return (
    <span className={`rounded-full border px-3 py-1 text-xs font-semibold capitalize backdrop-blur ${toneMap[tone]}`}>
      {label.replaceAll("_", " ")}
    </span>
  );
}
