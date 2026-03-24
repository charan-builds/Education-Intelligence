"use client";

import React from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import SurfaceCard from "@/components/ui/SurfaceCard";

type PieDatum = {
  name: string;
  value: number;
};

const PIE_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#06b6d4", "#f43f5e"];

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
              >
                {data.map((entry, index) => (
                  <Cell key={`${entry.name}-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  borderRadius: 16,
                  border: "1px solid rgba(148,163,184,0.18)",
                  background: "rgba(15,23,42,0.92)",
                  color: "#e2e8f0",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="space-y-3">
          {data.map((entry, index) => (
            <div key={entry.name} className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white/70 px-3 py-2 dark:border-slate-700 dark:bg-slate-900/70">
              <span
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }}
              />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{entry.name}</p>
              </div>
              <span className="text-sm text-slate-600 dark:text-slate-400">{entry.value}</span>
            </div>
          ))}
        </div>
      </div>
    </SurfaceCard>
  );
}
