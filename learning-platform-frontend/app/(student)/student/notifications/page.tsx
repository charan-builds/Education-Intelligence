"use client";

import { Bell, BrainCircuit } from "lucide-react";

import ActivityFeed from "@/components/dashboard/ActivityFeed";
import RecommendationPanel from "@/components/dashboard/RecommendationPanel";
import PageHeader from "@/components/layouts/PageHeader";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useStudentDashboard } from "@/hooks/useDashboard";

export default function StudentNotificationsPage() {
  const dashboard = useStudentDashboard();

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Notifications"
        title="Mentor alerts and next-step guidance"
        description="This inbox surfaces mentor notifications and recommendation text from the backend mentor modules."
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard title="Alerts" value={dashboard.notifications.length} tone="info" icon={<Bell className="h-5 w-5" />} />
        <MetricCard title="High priority" value={dashboard.kpis.highPriorityNotifications} tone="warning" />
        <MetricCard title="Recommendations" value={dashboard.recommendations.length} tone="success" icon={<BrainCircuit className="h-5 w-5" />} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <ActivityFeed
          title="Alert stream"
          description="Mentor notifications built from roadmap deadlines and weak-topic signals."
          items={dashboard.notifications.map((item) => ({
            title: item.title,
            subtitle: item.message,
            tone: item.severity,
          }))}
        />
        <RecommendationPanel
          title="Suggested guidance"
          description="Concise recommendations and focus prompts."
          items={dashboard.recommendations}
        />
      </div>

      <SurfaceCard title="Focus topics" description="Largest current gaps according to mentor progress analysis.">
        <div className="grid gap-3 md:grid-cols-2">
          {dashboard.weakTopics.map((item) => (
            <div
              key={item.topicId}
              className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
            >
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{item.name}</p>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                Improvement gap: {item.gap.toFixed(0)} points
              </p>
            </div>
          ))}
        </div>
      </SurfaceCard>
    </div>
  );
}
