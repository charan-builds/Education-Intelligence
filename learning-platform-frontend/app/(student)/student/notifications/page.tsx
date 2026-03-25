"use client";

import { useQuery } from "@tanstack/react-query";
import { Bell, BrainCircuit } from "lucide-react";

import ActivityFeed from "@/components/dashboard/ActivityFeed";
import RecommendationPanel from "@/components/dashboard/RecommendationPanel";
import PageHeader from "@/components/layouts/PageHeader";
import { useRealtime } from "@/components/providers/RealtimeProvider";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useAdaptiveStudentUI } from "@/hooks/useAdaptiveStudentUI";
import { useStudentDashboard } from "@/hooks/useDashboard";
import { getNotifications } from "@/services/notificationService";

export default function StudentNotificationsPage() {
  const dashboard = useStudentDashboard();
  const adaptiveUI = useAdaptiveStudentUI(dashboard);
  const { liveNotifications } = useRealtime();
  const notificationsQuery = useQuery({
    queryKey: ["notifications"],
    queryFn: () => getNotifications(false),
  });
  const persistedNotifications = notificationsQuery.data?.notifications ?? [];
  const notificationItems = [...liveNotifications, ...persistedNotifications]
    .filter((item, index, current) => current.findIndex((candidate) => candidate.id === item.id) === index)
    .slice(0, 8);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Notifications"
        title="Adaptive alerts and guidance"
        description="This inbox prioritizes prompts from your current behavior, progress pressure, and mentor intelligence."
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard title="Alerts" value={notificationItems.length + adaptiveUI.smartNotifications.length} tone="info" icon={<Bell className="h-5 w-5" />} />
        <MetricCard title="Adaptive tone" value={adaptiveUI.emotionalState.label} tone="warning" />
        <MetricCard title="Recommendations" value={dashboard.recommendations.length} tone="success" icon={<BrainCircuit className="h-5 w-5" />} />
      </div>

      {adaptiveUI.smartNotifications.length > 0 ? (
        <SurfaceCard title="Behavior-driven prompts" description="These notifications are generated from retention pressure, momentum, and current friction.">
          <div className="grid gap-3 md:grid-cols-3">
            {adaptiveUI.smartNotifications.map((item) => (
              <div key={item.title} className="story-card">
                <p className="text-sm font-semibold text-slate-950">{item.title}</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">{item.message}</p>
              </div>
            ))}
          </div>
        </SurfaceCard>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <ActivityFeed
          title="Alert stream"
          description="Mentor and adaptive notifications ranked by what matters now."
          items={[...adaptiveUI.smartNotifications, ...notificationItems.map((item) => ({
            title: item.title,
            message: item.message,
            severity: item.severity,
          }))].map((item) => ({
            title: item.title,
            subtitle: item.message,
            tone: item.severity,
          })).slice(0, 8)}
        />
        <RecommendationPanel
          title="Next best guidance"
          description="The top recommendation reflects current state before generic suggestions."
          items={[
            {
              title: adaptiveUI.nextBestAction.title,
              message: adaptiveUI.nextBestAction.description,
              why: "This action is ranked highest from the current adaptive UI model.",
              confidenceLabel: "Best next action",
              tone: "success" as const,
            },
            ...dashboard.recommendations,
          ].slice(0, 5)}
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
