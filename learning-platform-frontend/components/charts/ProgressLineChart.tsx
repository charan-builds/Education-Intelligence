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
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.22)" />
            <XAxis dataKey="label" tickLine={false} axisLine={false} />
            <YAxis domain={[0, 100]} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{
                borderRadius: 16,
                border: "1px solid rgba(148,163,184,0.18)",
                background: "rgba(15,23,42,0.92)",
                color: "#e2e8f0",
              }}
            />
            <Line
              type="monotone"
              dataKey="progress"
              stroke="#6366f1"
              strokeWidth={3}
              dot={{ fill: "#8b5cf6", strokeWidth: 0, r: 4 }}
              activeDot={{ r: 6 }}
              animationDuration={900}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {data.length > 0 ? (
        <div className="mt-4 rounded-[24px] border border-white/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.92),rgba(224,231,255,0.68))] p-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Milestone progress</p>
            <p className="text-sm font-semibold text-slate-950">{Math.round(data[data.length - 1]?.progress ?? 0)}%</p>
          </div>
          <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-200/80">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.max(0, Math.min(100, data[data.length - 1]?.progress ?? 0))}%` }}
              transition={{ duration: 0.9, ease: "easeOut" }}
              className="h-full rounded-full bg-[linear-gradient(90deg,#4f46e5,#0ea5e9,#34d399)]"
            />
          </div>
        </div>
      ) : null}
    </SurfaceCard>
  );
}
