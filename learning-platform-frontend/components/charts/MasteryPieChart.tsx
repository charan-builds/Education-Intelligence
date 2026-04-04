"use client";

import React from "react";
import { motion } from "framer-motion";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import SurfaceCard from "@/components/ui/SurfaceCard";

type PieDatum = {
  name: string;
  value: number;
};

const PIE_COLORS = ["#6C5CE7", "#8B5CF6", "#A29BFE", "#C084FC", "#DDD6FE"];

type MasteryPieChartProps = {
  title: string;
  description: string;
  data: PieDatum[];
};

export default function MasteryPieChart({
  title,
  description,
  data,
}: MasteryPieChartProps) {
  return (
    <SurfaceCard title={title} description={description}>
      <div className="grid gap-6 lg:grid-cols-[1fr_180px] lg:items-center">
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                innerRadius={70}
                outerRadius={105}
                paddingAngle={2}
                nameKey="name"
                animationDuration={900}
              >
                {data.map((entry, index) => (
                  <Cell key={`${entry.name}-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  borderRadius: 16,
                  border: "1px solid rgba(162,155,254,0.24)",
                  background: "rgba(76,29,149,0.94)",
                  color: "#f5f3ff",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="space-y-3">
          {data.map((entry, index) => (
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.25, delay: index * 0.04 }}
              key={entry.name}
              className="flex items-center gap-3 rounded-2xl border border-violet-200/70 bg-white/75 px-3 py-2 dark:border-violet-500/20 dark:bg-violet-950/55"
            >
              <span
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }}
              />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-violet-950 dark:text-violet-50">{entry.name}</p>
              </div>
              <span className="text-sm text-violet-700/80 dark:text-violet-100/72">{entry.value}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </SurfaceCard>
  );
}
