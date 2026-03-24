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
    <div className="rounded-[28px] border border-rose-200 bg-rose-50/90 p-6 dark:border-rose-500/30 dark:bg-rose-500/10">
      <div className="flex gap-4">
        <div className="mt-0.5 flex h-10 w-10 items-center justify-center rounded-2xl bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-200">
          <AlertTriangle className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-lg font-semibold text-rose-900 dark:text-rose-100">{title}</h3>
          <p className="mt-2 text-sm leading-7 text-rose-800 dark:text-rose-200/90">{description}</p>
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
