"use client";

import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import SurfaceCard from "@/components/ui/SurfaceCard";
import type { RoadmapStep } from "@/types/roadmap";

const PIE_COLORS = ["#10b981", "#f59e0b", "#94a3b8"];

function normalizeStatus(status: string): "completed" | "in_progress" | "pending" {
  const value = status.toLowerCase();
  if (value === "completed") {
    return "completed";
  }
  if (value === "in_progress") {
    return "in_progress";
  }
  return "pending";
}

export default function ProgressCharts({ steps }: { steps: RoadmapStep[] }) {
  const progressLineData = steps.map((step, index) => {
    const completedUntilNow = steps.slice(0, index + 1).filter((s) => normalizeStatus(s.progress_status) === "completed").length;
    const percent = index + 1 > 0 ? Math.round((completedUntilNow / (index + 1)) * 100) : 0;
    return {
      topic: `T${step.topic_id}`,
      progress: percent,
    };
  });

  const difficultyBucket = { easy: 0, medium: 0, hard: 0, expert: 0 };
  for (const step of steps) {
    const key = step.difficulty.toLowerCase();
    if (key in difficultyBucket) {
      difficultyBucket[key as keyof typeof difficultyBucket] += 1;
    }
  }

  const difficultyBarData = [
    { difficulty: "easy", count: difficultyBucket.easy },
    { difficulty: "medium", count: difficultyBucket.medium },
    { difficulty: "hard", count: difficultyBucket.hard },
    { difficulty: "expert", count: difficultyBucket.expert },
  ];

  const statusPieData = [
    { name: "Completed", value: steps.filter((step) => normalizeStatus(step.progress_status) === "completed").length },
    { name: "In Progress", value: steps.filter((step) => normalizeStatus(step.progress_status) === "in_progress").length },
    { name: "Pending", value: steps.filter((step) => normalizeStatus(step.progress_status) === "pending").length },
  ];

  return (
    <>
      <div className="grid gap-6 xl:grid-cols-2">
        <SurfaceCard title="Roadmap Progress Trend" description="Trend line derived from ordered roadmap steps and their completion state.">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={progressLineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="topic" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="progress" stroke="#0ea5e9" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </SurfaceCard>

        <SurfaceCard title="Topic Status Breakdown" description="Distribution of roadmap step completion states.">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={statusPieData} dataKey="value" nameKey="name" outerRadius={100} label>
                  {statusPieData.map((_, index) => (
                    <Cell key={`status-cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </SurfaceCard>
      </div>

      <SurfaceCard title="Difficulty Distribution" description="Difficulty spread for the current roadmap workload.">
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={difficultyBarData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="difficulty" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#0ea5e9" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </SurfaceCard>
    </>
  );
}
