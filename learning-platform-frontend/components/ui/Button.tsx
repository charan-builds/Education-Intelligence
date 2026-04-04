"use client";

import React from "react";

import { cn } from "@/utils/cn";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
};

export default function Button({
  className,
  variant = "primary",
  type = "button",
  ...props
}: ButtonProps) {
  const variantClasses = {
    primary:
      "workspace-button-primary text-white hover:-translate-y-0.5",
    secondary:
      "border border-violet-200/80 bg-white/88 text-violet-950 shadow-sm shadow-violet-200/40 backdrop-blur-sm hover:-translate-y-0.5 hover:border-violet-300 hover:bg-white dark:border-violet-400/20 dark:bg-violet-950/55 dark:text-violet-100 dark:hover:bg-violet-900/70",
    ghost:
      "text-violet-700 hover:bg-violet-100/80 hover:text-violet-900 dark:text-violet-200 dark:hover:bg-violet-900/70 dark:hover:text-violet-50",
    danger:
      "bg-gradient-to-r from-violet-700 via-purple-700 to-fuchsia-700 text-white shadow-sm shadow-violet-400/30 hover:-translate-y-0.5 hover:from-violet-600 hover:via-purple-600 hover:to-fuchsia-600",
  } as const;

  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-semibold transition duration-200 disabled:cursor-not-allowed disabled:opacity-60",
        variantClasses[variant],
        className,
      )}
      {...props}
    />
  );
}
