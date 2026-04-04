"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import SurfaceCard from "@/components/ui/SurfaceCard";

type ProgressPoint = {
  label: string;
  progress: number;
};

type ProgressLineChartProps = {
  title: string;
  description: string;
  data: ProgressPoint[];
};

export default function ProgressLineChart({
  title,
  description,
  data,
}: ProgressLineChartProps) {
  return (
    <SurfaceCard title={title} description={description}>
      <div className="h-72 min-w-0">
        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={288}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(162,155,254,0.24)" />
            <XAxis dataKey="label" tickLine={false} axisLine={false} />
            <YAxis domain={[0, 100]} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{
                borderRadius: 16,
                border: "1px solid rgba(162,155,254,0.24)",
                background: "rgba(76,29,149,0.94)",
                color: "#f5f3ff",
              }}
            />
            <Line
              type="monotone"
              dataKey="progress"
              stroke="#6C5CE7"
              strokeWidth={3}
              dot={{ fill: "#A29BFE", strokeWidth: 0, r: 4 }}
              activeDot={{ r: 6 }}
              animationDuration={900}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {data.length > 0 ? (
        <div className="mt-4 rounded-[24px] border border-violet-200/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.94),rgba(237,233,254,0.82))] p-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-violet-500">Milestone progress</p>
            <p className="text-sm font-semibold text-violet-950">{Math.round(data[data.length - 1]?.progress ?? 0)}%</p>
          </div>
          <div className="mt-3 h-3 overflow-hidden rounded-full bg-violet-100/90">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.max(0, Math.min(100, data[data.length - 1]?.progress ?? 0))}%` }}
              transition={{ duration: 0.9, ease: "easeOut" }}
              className="h-full rounded-full bg-[linear-gradient(90deg,#6C5CE7,#8B5CF6,#C084FC)]"
            />
          </div>
        </div>
      ) : null}
    </SurfaceCard>
  );
}
