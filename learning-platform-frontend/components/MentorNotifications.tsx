"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/services/apiClient";

type MentorNotificationItem = {
  trigger: string;
  severity: "low" | "medium" | "high" | string;
  title: string;
  message: string;
};

type MentorNotificationsResponse = {
  notifications: MentorNotificationItem[];
};

async function getMentorNotifications(): Promise<MentorNotificationsResponse> {
  const { data } = await apiClient.get<MentorNotificationsResponse>("/mentor/notifications");
  return data;
}

function severityClass(severity: string): string {
  const value = severity.toLowerCase();
  if (value === "high") {
    return "bg-rose-100 text-rose-700";
  }
  if (value === "medium") {
    return "bg-amber-100 text-amber-700";
  }
  return "bg-emerald-100 text-emerald-700";
}

export default function MentorNotifications() {
  const query = useQuery({
    queryKey: ["mentor-notifications"],
    queryFn: getMentorNotifications,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  const metrics = useMemo(() => {
    const items = query.data?.notifications ?? [];
    const high = items.filter((item) => item.severity.toLowerCase() === "high").length;
    return { total: items.length, high };
  }, [query.data?.notifications]);

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-slate-900">Mentor Notifications</h2>
        <div className="flex items-center gap-2 text-xs">
          <span className="rounded-full bg-slate-100 px-2 py-1 font-semibold text-slate-700">{metrics.total} total</span>
          <span className="rounded-full bg-rose-100 px-2 py-1 font-semibold text-rose-700">{metrics.high} high</span>
        </div>
      </div>

      {query.isLoading && <p className="mt-3 text-sm text-slate-600">Loading notifications...</p>}
      {query.isError && <p className="mt-3 text-sm text-red-600">Failed to load notifications.</p>}

      {!query.isLoading && !query.isError && (query.data?.notifications.length ?? 0) === 0 && (
        <p className="mt-3 text-sm text-slate-600">No notifications right now.</p>
      )}

      <ul className="mt-3 space-y-2">
        {(query.data?.notifications ?? []).map((item, index) => (
          <li key={`${item.trigger}-${index}`} className="rounded-lg border border-slate-200 p-3">
            <div className="flex items-center justify-between gap-3">
              <p className="font-medium text-slate-900">{item.title}</p>
              <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${severityClass(item.severity)}`}>
                {item.severity}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-700">{item.message}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
