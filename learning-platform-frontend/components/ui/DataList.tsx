"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

import EmptyState from "@/components/ui/EmptyState";
import { cn } from "@/utils/cn";

type DataListProps<T> = {
  items: T[];
  emptyTitle: string;
  emptyDescription: string;
  getKey: (item: T, index: number) => string;
  renderItem: (item: T, index: number) => ReactNode;
  className?: string;
  itemClassName?: string;
};

export default function DataList<T>({
  items,
  emptyTitle,
  emptyDescription,
  getKey,
  renderItem,
  className,
  itemClassName,
}: DataListProps<T>) {
  if (items.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  return (
    <div className={cn("space-y-3", className)}>
      {items.map((item, index) => (
        <motion.div
          key={getKey(item, index)}
          initial={{ opacity: 0, y: 8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.15 }}
          transition={{ duration: 0.22, delay: index * 0.03 }}
          className={cn(
            "rounded-[22px] border border-violet-200/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.92),rgba(245,243,255,0.78))] px-4 py-3 shadow-[0_16px_40px_-34px_rgba(109,40,217,0.45)] backdrop-blur dark:border-violet-500/20 dark:bg-violet-950/55",
            itemClassName,
          )}
        >
          {renderItem(item, index)}
        </motion.div>
      ))}
    </div>
  );
}
