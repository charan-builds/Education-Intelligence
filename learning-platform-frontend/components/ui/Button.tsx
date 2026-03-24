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
      "bg-gradient-to-r from-brand-700 via-brand-600 to-brand-500 text-white shadow-glow hover:brightness-105",
    secondary:
      "border border-slate-200 bg-white/90 text-slate-900 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800",
    ghost:
      "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800",
    danger:
      "bg-rose-600 text-white hover:bg-rose-500",
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
