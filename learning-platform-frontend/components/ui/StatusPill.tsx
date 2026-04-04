import React from "react";

type StatusPillProps = {
  label: string;
  tone?: "default" | "success" | "warning" | "danger";
};

export default function StatusPill({ label, tone = "default" }: StatusPillProps) {
  const toneMap = {
    default: "border-violet-200 bg-violet-50/90 text-violet-700 dark:border-violet-700/60 dark:bg-violet-900/40 dark:text-violet-200",
    success: "border-violet-300 bg-violet-100/90 text-violet-700 dark:border-violet-500/30 dark:bg-violet-500/15 dark:text-violet-200",
    warning: "border-fuchsia-200 bg-fuchsia-50/90 text-fuchsia-700 dark:border-fuchsia-500/30 dark:bg-fuchsia-500/15 dark:text-fuchsia-200",
    danger: "border-rose-200 bg-rose-50/90 text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/15 dark:text-rose-200",
  } as const;

  return (
    <span className={`rounded-full border px-3 py-1.5 text-xs font-semibold capitalize backdrop-blur transition duration-200 ${toneMap[tone]}`}>
      {label.replaceAll("_", " ")}
    </span>
  );
}
