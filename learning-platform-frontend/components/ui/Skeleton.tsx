"use client";

import { cn } from "@/utils/cn";

type SkeletonProps = {
  className?: string;
};

export default function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl bg-violet-200/55 dark:bg-violet-900/45",
        "before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_1.8s_infinite]",
        "before:bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.72),transparent)] dark:before:bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.14),transparent)]",
        className,
      )}
    />
  );
}
