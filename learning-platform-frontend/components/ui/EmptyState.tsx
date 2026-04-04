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
    <div className="rounded-[28px] border border-dashed border-violet-200/90 bg-white/76 p-8 text-center shadow-[0_24px_60px_-34px_rgba(109,40,217,0.28)] backdrop-blur dark:border-violet-500/20 dark:bg-violet-950/50">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-violet-100 text-violet-700 shadow-[0_10px_30px_rgba(124,58,237,0.16)] dark:bg-violet-500/10 dark:text-violet-100">
        <Sparkles className="h-6 w-6" />
      </div>
      <h3 className="mt-4 text-xl font-semibold text-violet-950 dark:text-violet-50">{title}</h3>
      <p className="mt-2 text-sm leading-7 text-violet-800/78 dark:text-violet-100/72">{description}</p>
      {actionLabel && onAction ? (
        <Button className="mt-5" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
