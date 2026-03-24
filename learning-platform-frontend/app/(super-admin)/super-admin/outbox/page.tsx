"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import PageHeader from "@/components/layouts/PageHeader";
import { useToast } from "@/components/providers/ToastProvider";
import Button from "@/components/ui/Button";
import Select from "@/components/ui/Select";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { flushOutbox, getOutboxEvents, getOutboxStats, recoverStuckOutbox, requeueDeadOutbox } from "@/services/opsService";

export default function SuperAdminOutboxPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<"pending" | "processing" | "dead" | "dispatched">("dead");

  const statsQuery = useQuery({
    queryKey: ["super-admin", "outbox", "stats"],
    queryFn: getOutboxStats,
    refetchInterval: 30_000,
  });
  const eventsQuery = useQuery({
    queryKey: ["super-admin", "outbox", status],
    queryFn: () => getOutboxEvents({ event_status: status, limit: 25, offset: 0 }),
  });

  const flushMutation = useMutation({
    mutationFn: () => flushOutbox(),
    onSuccess: async () => {
      toast({ title: "Outbox flush queued", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["super-admin", "outbox"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard", "super-admin"] });
    },
  });

  const requeueMutation = useMutation({
    mutationFn: () => requeueDeadOutbox(),
    onSuccess: async () => {
      toast({ title: "Dead events requeued", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["super-admin", "outbox"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard", "super-admin"] });
    },
  });

  const recoverMutation = useMutation({
    mutationFn: () => recoverStuckOutbox(),
    onSuccess: async () => {
      toast({ title: "Stuck events recovered", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["super-admin", "outbox"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard", "super-admin"] });
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Super admin"
        title="Outbox monitoring"
        description="Inspect event backlog health and run operational recovery actions."
      />

      <SurfaceCard title="Outbox controls" description="Run recovery actions backed by the ops routes.">
        <div className="flex flex-wrap gap-3">
          <Button onClick={() => flushMutation.mutate()} disabled={flushMutation.isPending}>
            Flush pending
          </Button>
          <Button onClick={() => requeueMutation.mutate()} disabled={requeueMutation.isPending} variant="secondary">
            Requeue dead
          </Button>
          <Button onClick={() => recoverMutation.mutate()} disabled={recoverMutation.isPending} variant="ghost">
            Recover stuck
          </Button>
        </div>
      </SurfaceCard>

      <div className="grid gap-6 xl:grid-cols-[0.75fr_1.25fr]">
        <SurfaceCard title="Status snapshot" description="Current backlog counts from `/ops/outbox/stats`.">
          <div className="grid gap-3">
            {Object.entries(statsQuery.data ?? {}).map(([key, value]) => (
              <div key={key} className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70">
                <p className="text-sm font-semibold capitalize text-slate-900 dark:text-slate-100">{key}</p>
                <p className="mt-2 text-3xl font-semibold text-slate-950 dark:text-slate-50">{value}</p>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard
          title="Outbox events"
          description="Filter live events by status to inspect retries and dead letters."
          actions={
            <Select value={status} onChange={(event) => setStatus(event.target.value as typeof status)} className="min-w-[180px]">
              <option value="dead">dead</option>
              <option value="pending">pending</option>
              <option value="processing">processing</option>
              <option value="dispatched">dispatched</option>
            </Select>
          }
        >
          <div className="space-y-3">
            {(eventsQuery.data?.items ?? []).map((event) => (
              <div
                key={event.id}
                className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
              >
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{event.event_type}</p>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                  status={event.status} • attempts={event.attempts} • tenant={event.tenant_id ?? "platform"}
                </p>
                {event.error_message ? (
                  <p className="mt-2 text-sm text-rose-700 dark:text-rose-200">{event.error_message}</p>
                ) : null}
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}
