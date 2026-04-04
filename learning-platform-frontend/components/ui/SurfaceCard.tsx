import React, { type ReactNode } from "react";

type SurfaceCardProps = {
  title: string;
  description?: string;
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
};

export default function SurfaceCard({ title, description, actions, children, className }: SurfaceCardProps) {
  return (
    <section
      className={[
        "glass-surface soft-ring rounded-[34px] border border-white/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.95))] p-6 shadow-[0_26px_70px_-34px_rgba(15,23,42,0.24)] dark:border-violet-400/15 dark:bg-[linear-gradient(180deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))]",
        className ?? "",
      ].join(" ")}
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-xl font-semibold tracking-tight text-slate-950 dark:text-violet-50">{title}</h2>
          {description ? <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-violet-200/80">{description}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}
