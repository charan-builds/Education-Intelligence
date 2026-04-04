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
        "glass-surface soft-ring rounded-[34px] p-6 shadow-[0_22px_60px_-32px_rgba(109,40,217,0.35)] dark:border-violet-400/15",
        className ?? "",
      ].join(" ")}
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-xl font-semibold tracking-tight text-violet-950 dark:text-violet-50">{title}</h2>
          {description ? <p className="mt-2 text-sm leading-7 text-violet-700/85 dark:text-violet-200/80">{description}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}
