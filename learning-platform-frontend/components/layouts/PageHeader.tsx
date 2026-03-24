"use client";

import { motion } from "framer-motion";
import React, { ReactNode } from "react";

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
  meta?: ReactNode;
};

export default function PageHeader({ eyebrow, title, description, actions, meta }: PageHeaderProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="mesh-panel soft-ring relative overflow-hidden rounded-[38px] border border-white/60 p-7 shadow-panel dark:border-slate-700/80"
    >
      <div className="absolute inset-y-0 right-0 w-1/2 bg-[radial-gradient(circle_at_top_right,_rgba(255,255,255,0.32),_transparent_52%)]" />
      <div className="absolute -right-10 top-10 h-36 w-36 rounded-full bg-white/20 blur-3xl" />
      <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-brand-700 dark:text-brand-100">{eyebrow}</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 dark:text-slate-50 md:text-5xl">
            {title}
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">{description}</p>
          {meta ? <div className="mt-5 flex flex-wrap gap-3">{meta}</div> : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      </div>
    </motion.section>
  );
}
