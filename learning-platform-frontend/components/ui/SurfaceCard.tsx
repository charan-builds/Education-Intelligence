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
        "glass-surface soft-ring rounded-[34px] p-6 dark:border-slate-700",
        className ?? "",
      ].join(" ")}
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-xl font-semibold tracking-tight text-slate-950 dark:text-slate-100">{title}</h2>
          {description ? <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-400">{description}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}
