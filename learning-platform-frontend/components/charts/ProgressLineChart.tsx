"use client";

import React from "react";
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
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </SurfaceCard>
  );
}
