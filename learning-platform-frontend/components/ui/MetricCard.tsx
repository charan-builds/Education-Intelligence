import React, { type ReactNode } from "react";

type MetricCardProps = {
  eyebrow?: string;
  title: string;
  value: string | number;
  description?: string;
  tone?: "default" | "info" | "success" | "warning";
  delta?: string;
  icon?: ReactNode;
};

export default function MetricCard({
  eyebrow,
  title,
  value,
  description,
  tone = "default",
  delta,
  icon,
}: MetricCardProps) {
  const toneMap = {
    default:
      "border-violet-200/80 from-white via-violet-50 to-fuchsia-50/80 text-violet-950 dark:from-violet-950 dark:via-violet-950 dark:to-violet-900 dark:text-violet-100",
    info: "border-violet-300/30 from-violet-600 via-purple-600 to-fuchsia-500 text-white",
    success: "border-violet-300/30 from-violet-500 via-purple-500 to-indigo-500 text-white",
    warning: "border-fuchsia-200/60 from-fuchsia-200 via-violet-200 to-purple-200 text-violet-950",
  } as const;

  const darkTextClass = tone === "default" ? "text-slate-950 dark:text-slate-100" : "text-current";
  const mutedTextClass =
    tone === "default"
      ? "text-slate-600 dark:text-slate-400"
      : tone === "warning"
        ? "text-violet-900/75"
        : "text-white/80";

  return (
    <article
      className={`soft-ring rounded-[30px] border bg-gradient-to-br ${toneMap[tone]} p-6 shadow-panel transition duration-300 hover:-translate-y-1.5 hover:shadow-[0_24px_60px_rgba(124,58,237,0.18)]`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          {eyebrow ? <p className={`text-xs font-semibold uppercase tracking-[0.24em] ${mutedTextClass}`}>{eyebrow}</p> : null}
          <p className={`mt-2 text-sm font-medium ${mutedTextClass}`}>{title}</p>
        </div>
        {icon ? (
          <div className="rounded-[18px] border border-white/20 bg-white/15 p-3 backdrop-blur">
            <div className={mutedTextClass}>{icon}</div>
          </div>
        ) : null}
      </div>
      <div className="mt-5 flex items-end justify-between gap-4">
        <p className={`text-3xl font-semibold tracking-tight ${darkTextClass}`}>{value}</p>
        {delta ? (
          <span className="rounded-full bg-white/20 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] backdrop-blur dark:bg-black/10">
            {delta}
          </span>
        ) : null}
      </div>
      {description ? <p className={`mt-2 text-sm leading-6 ${mutedTextClass}`}>{description}</p> : null}
    </article>
  );
}
