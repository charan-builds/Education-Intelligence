"use client";

import Link from "next/link";
import { ArrowUpRight, type LucideIcon } from "lucide-react";

type QuickLinkCardProps = {
  href: string;
  title: string;
  description: string;
  icon: LucideIcon;
};

export default function QuickLinkCard({ href, title, description, icon: Icon }: QuickLinkCardProps) {
  return (
    <Link
      href={href}
      className="group rounded-[28px] border border-violet-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(245,243,255,0.84))] p-5 shadow-[0_20px_60px_-36px_rgba(109,40,217,0.28)] transition duration-300 hover:-translate-y-1.5 hover:border-violet-300 hover:shadow-[0_28px_80px_-38px_rgba(109,40,217,0.38)] dark:border-violet-500/20 dark:bg-violet-950/60"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-[18px] bg-[linear-gradient(135deg,#6C5CE7,#A29BFE)] text-white shadow-[0_18px_40px_-24px_rgba(108,92,231,0.65)]">
          <Icon className="h-5 w-5" />
        </div>
        <ArrowUpRight className="h-4 w-4 text-violet-400 transition group-hover:text-violet-600" />
      </div>
      <p className="mt-5 text-base font-semibold text-violet-950 dark:text-violet-50">{title}</p>
      <p className="mt-2 text-sm leading-7 text-violet-800/78 dark:text-violet-100/72">{description}</p>
    </Link>
  );
}
