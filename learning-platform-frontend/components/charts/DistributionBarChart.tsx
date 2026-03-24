"use client";

import React from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import SurfaceCard from "@/components/ui/SurfaceCard";

type DistributionDatum = {
  label: string;
  value: number;
};

type DistributionBarChartProps = {
  title: string;
  description: string;
  data: DistributionDatum[];
};

export default function DistributionBarChart({
  title,
  description,
  data,
}: DistributionBarChartProps) {
  return (
    <SurfaceCard title={title} description={description}>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.22)" />
            <XAxis dataKey="label" tickLine={false} axisLine={false} />
            <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{
                borderRadius: 16,
                border: "1px solid rgba(148,163,184,0.18)",
                background: "rgba(15,23,42,0.92)",
                color: "#e2e8f0",
              }}
            />
            <Bar dataKey="value" fill="url(#barFill)" radius={[12, 12, 0, 0]} />
            <defs>
              <linearGradient id="barFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#8b5cf6" />
                <stop offset="100%" stopColor="#06b6d4" />
              </linearGradient>
            </defs>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </SurfaceCard>
  );
}
