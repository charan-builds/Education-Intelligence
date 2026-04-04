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
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(162,155,254,0.24)" />
            <XAxis dataKey="label" tickLine={false} axisLine={false} />
            <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{
                borderRadius: 16,
                border: "1px solid rgba(162,155,254,0.24)",
                background: "rgba(76,29,149,0.94)",
                color: "#f5f3ff",
              }}
            />
            <Bar dataKey="value" fill="url(#barFill)" radius={[12, 12, 0, 0]} />
            <defs>
              <linearGradient id="barFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#6C5CE7" />
                <stop offset="100%" stopColor="#A29BFE" />
              </linearGradient>
            </defs>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </SurfaceCard>
  );
}
