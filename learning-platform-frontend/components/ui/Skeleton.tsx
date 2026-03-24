"use client";

import { cn } from "@/utils/cn";

type SkeletonProps = {
  className?: string;
};

export default function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl bg-slate-200/70 dark:bg-slate-800/80",
        "before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_1.8s_infinite]",
        "before:bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.55),transparent)] dark:before:bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.08),transparent)]",
        className,
      )}
    />
  );
}
