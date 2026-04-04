"use client";

import React from "react";
import Image from "next/image";

import { cn } from "@/utils/cn";

type LogoProps = {
  className?: string;
  showWordmark?: boolean;
  labelClassName?: string;
};

export default function Logo({ className, showWordmark = true, labelClassName }: LogoProps) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div className="relative h-12 w-12 overflow-hidden rounded-[18px] shadow-[0_16px_40px_rgba(15,23,42,0.22)] ring-1 ring-white/30">
        <Image src="/assets/logo.svg" alt="Learnova AI logo" fill sizes="48px" priority className="object-cover" />
      </div>
      {showWordmark ? (
        <div className={labelClassName}>
          <p className="text-[11px] font-semibold uppercase tracking-[0.34em] text-brand-700 dark:text-violet-200">Learnova AI</p>
          <p className="text-lg font-semibold tracking-tight text-slate-950 dark:text-slate-100">Adaptive Learning Intelligence</p>
        </div>
      ) : null}
    </div>
  );
}
