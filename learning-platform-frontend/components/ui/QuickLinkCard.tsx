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
      className="group rounded-[28px] border border-slate-200/85 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(240,249,255,0.92))] p-5 shadow-[0_20px_60px_-36px_rgba(15,23,42,0.18)] transition duration-300 hover:-translate-y-1.5 hover:border-sky-300 hover:shadow-[0_28px_80px_-38px_rgba(14,165,233,0.26)] dark:border-slate-700/60 dark:bg-[linear-gradient(180deg,rgba(15,23,42,0.94),rgba(2,6,23,0.94))]"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-[18px] bg-[linear-gradient(135deg,#0ea5e9,#14b8a6)] text-white shadow-[0_18px_40px_-24px_rgba(14,165,233,0.48)]">
          <Icon className="h-5 w-5" />
        </div>
        <ArrowUpRight className="h-4 w-4 text-slate-400 transition group-hover:text-sky-600" />
      </div>
      <p className="mt-5 text-base font-semibold text-slate-950 dark:text-slate-50">{title}</p>
      <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">{description}</p>
    </Link>
  );
}
