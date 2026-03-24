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
      "border-white/70 from-white via-slate-50 to-indigo-50/70 text-slate-950 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800 dark:text-slate-100",
    info: "border-indigo-300/30 from-indigo-600 via-violet-600 to-cyan-500 text-white",
    success: "border-emerald-300/30 from-emerald-500 via-teal-500 to-cyan-500 text-white",
    warning: "border-amber-200/60 from-amber-300 via-orange-300 to-rose-300 text-slate-950",
  } as const;

  const darkTextClass = tone === "default" ? "text-slate-950 dark:text-slate-100" : "text-current";
  const mutedTextClass =
    tone === "default"
      ? "text-slate-600 dark:text-slate-400"
      : tone === "warning"
        ? "text-slate-800/80"
        : "text-white/80";

  return (
    <article
      className={`soft-ring rounded-[30px] border bg-gradient-to-br ${toneMap[tone]} p-5 shadow-panel transition duration-200 hover:-translate-y-1.5 hover:shadow-[0_24px_60px_rgba(79,70,229,0.12)]`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          {eyebrow ? <p className={`text-xs font-semibold uppercase tracking-[0.24em] ${mutedTextClass}`}>{eyebrow}</p> : null}
          <p className={`mt-2 text-sm font-medium ${mutedTextClass}`}>{title}</p>
        </div>
        {icon ? (
          <div className="rounded-[18px] border border-white/20 bg-white/15 p-2.5 backdrop-blur">
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
