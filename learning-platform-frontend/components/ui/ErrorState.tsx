"use client";

import { AlertTriangle } from "lucide-react";

import Button from "@/components/ui/Button";

type ErrorStateProps = {
  title?: string;
  description: string;
  onRetry?: () => void;
};

export default function ErrorState({
  title = "Something went wrong",
  description,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="rounded-[28px] border border-violet-200/90 bg-[linear-gradient(135deg,rgba(255,255,255,0.94),rgba(245,243,255,0.94))] p-6 shadow-[0_24px_60px_-34px_rgba(109,40,217,0.28)] dark:border-violet-500/20 dark:bg-violet-950/50">
      <div className="flex gap-4">
        <div className="mt-0.5 flex h-10 w-10 items-center justify-center rounded-2xl bg-violet-100 text-violet-700 dark:bg-violet-500/10 dark:text-violet-100">
          <AlertTriangle className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-lg font-semibold text-violet-950 dark:text-violet-50">{title}</h3>
          <p className="mt-2 text-sm leading-7 text-violet-800/82 dark:text-violet-100/78">{description}</p>
          {onRetry ? (
            <Button className="mt-4" variant="secondary" onClick={onRetry}>
              Try again
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
