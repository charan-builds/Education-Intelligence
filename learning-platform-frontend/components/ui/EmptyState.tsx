"use client";

import { Sparkles } from "lucide-react";

import Button from "@/components/ui/Button";

type EmptyStateProps = {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
};

export default function EmptyState({ title, description, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="rounded-[28px] border border-dashed border-slate-300 bg-white/70 p-8 text-center dark:border-slate-700 dark:bg-slate-900/70">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-brand-100 text-brand-700 dark:bg-brand-900/50 dark:text-brand-100">
        <Sparkles className="h-6 w-6" />
      </div>
      <h3 className="mt-4 text-xl font-semibold text-slate-950 dark:text-slate-100">{title}</h3>
      <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-400">{description}</p>
      {actionLabel && onAction ? (
        <Button className="mt-5" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
