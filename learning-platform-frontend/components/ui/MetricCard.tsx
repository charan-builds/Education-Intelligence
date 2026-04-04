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
      "border-slate-200/90 from-white via-slate-50 to-sky-50/70 text-slate-950 dark:from-slate-950 dark:via-slate-950 dark:to-slate-900 dark:text-slate-100",
    info: "border-sky-300/40 from-sky-600 via-cyan-600 to-blue-500 text-white",
    success: "border-emerald-300/40 from-emerald-600 via-teal-600 to-cyan-500 text-white",
    warning: "border-amber-200/70 from-amber-100 via-orange-100 to-rose-100 text-amber-950 dark:border-amber-500/20 dark:from-amber-500/15 dark:via-orange-500/10 dark:to-rose-500/10 dark:text-amber-100",
  } as const;

  const darkTextClass = tone === "default" ? "text-slate-950 dark:text-slate-100" : "text-current";
  const mutedTextClass =
    tone === "default"
      ? "text-slate-600 dark:text-slate-400"
      : tone === "warning"
        ? "text-amber-950/80 dark:text-amber-100/80"
        : "text-white/80";

  return (
    <article
      className={`soft-ring rounded-[30px] border bg-gradient-to-br ${toneMap[tone]} p-6 shadow-panel transition duration-300 hover:-translate-y-1.5 hover:shadow-[0_24px_60px_rgba(15,23,42,0.16)]`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          {eyebrow ? <p className={`text-xs font-semibold uppercase tracking-[0.24em] ${mutedTextClass}`}>{eyebrow}</p> : null}
          <p className={`mt-2 text-sm font-medium ${mutedTextClass}`}>{title}</p>
        </div>
        {icon ? (
          <div className="rounded-[18px] border border-white/25 bg-white/15 p-3 backdrop-blur dark:border-white/10">
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
