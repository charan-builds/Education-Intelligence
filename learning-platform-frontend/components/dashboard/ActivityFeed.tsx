"use client";

import { motion } from "framer-motion";
import React from "react";

import SurfaceCard from "@/components/ui/SurfaceCard";

type ActivityItem = {
  title: string;
  subtitle: string;
  tone?: string;
};

type ActivityFeedProps = {
  title?: string;
  description?: string;
  items: ActivityItem[];
};

function toneColor(tone?: string): string {
  if (tone === "high" || tone === "danger") {
    return "bg-rose-500";
  }
  if (tone === "warning" || tone === "in_progress") {
    return "bg-amber-500";
  }
  if (tone === "completed" || tone === "success") {
    return "bg-emerald-500";
  }
  return "bg-indigo-500";
}

export default function ActivityFeed({
  title = "Recent activity",
  description = "Live moments from the current workspace.",
  items,
}: ActivityFeedProps) {
  return (
    <SurfaceCard title={title} description={description}>
      <div className="space-y-3">
        {items.map((item, index) => (
          <motion.div
            key={`${item.title}-${index}`}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.04 }}
            className="flex items-start gap-3 rounded-[24px] border border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.9),rgba(248,250,255,0.76))] px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
          >
            <span className={`mt-1.5 h-2.5 w-2.5 rounded-full shadow-sm ${toneColor(item.tone)}`} />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{item.title}</p>
              <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-400">{item.subtitle}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </SurfaceCard>
  );
}
