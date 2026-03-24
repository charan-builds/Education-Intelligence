"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import PageHeader from "@/components/layouts/PageHeader";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { getHealth } from "@/services/healthService";
import { getOutboxStats } from "@/services/opsService";

export default function SuperAdminHealthPage() {
  const healthQuery = useQuery({
    queryKey: ["super-admin", "health"],
    queryFn: getHealth,
    refetchInterval: 15_000,
  });
  const outboxStatsQuery = useQuery({
    queryKey: ["super-admin", "health", "outbox"],
    queryFn: getOutboxStats,
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Super admin"
        title="System health"
        description="Quick platform health view anchored on `/health` plus outbox operational signals."
      />

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard title="API health" value={healthQuery.data?.status ?? "unknown"} tone="info" />
        <MetricCard title="Pending outbox" value={outboxStatsQuery.data?.pending ?? 0} tone="success" />
        <MetricCard title="Processing" value={outboxStatsQuery.data?.processing ?? 0} tone="warning" />
        <MetricCard title="Dead events" value={outboxStatsQuery.data?.dead ?? 0} />
      </div>

      <SurfaceCard title="Monitoring links" description="Local stack endpoints exposed by Docker Compose.">
        <div className="grid gap-4 md:grid-cols-3">
          {[
            { label: "Backend health", href: "http://localhost:8000/health" },
            { label: "Prometheus", href: "http://localhost:9090" },
            { label: "Grafana", href: "http://localhost:3001" },
          ].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-[28px] border border-slate-200 bg-white/75 p-5 text-sm font-semibold text-slate-900 dark:border-slate-700 dark:bg-slate-900/75 dark:text-slate-100"
            >
              {item.label}
            </Link>
          ))}
        </div>
      </SurfaceCard>
    </div>
  );
}
