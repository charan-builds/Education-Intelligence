"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BrainCircuit, Gauge, RefreshCcw, Workflow } from "lucide-react";

import PageHeader from "@/components/layouts/PageHeader";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { createFeatureSnapshot, getMlOverview, trainModel } from "@/services/mlService";

export default function AdminMlPage() {
  const queryClient = useQueryClient();
  const overviewQuery = useQuery({ queryKey: ["ml", "overview"], queryFn: getMlOverview });

  const refreshMutation = useMutation({
    mutationFn: createFeatureSnapshot,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["ml"] });
    },
  });

  const trainRecommendationMutation = useMutation({
    mutationFn: () => trainModel("recommendation_model"),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["ml"] });
    },
  });

  const trainDifficultyMutation = useMutation({
    mutationFn: () => trainModel("difficulty_prediction_model"),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["ml"] });
    },
  });

  const trainDropoutMutation = useMutation({
    mutationFn: () => trainModel("dropout_prediction_model"),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["ml"] });
    },
  });

  const overview = overviewQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="ML platform"
        title="Operate learning intelligence as a data product"
        description="Turn learner telemetry into reusable features, train models on schedule, version them explicitly, and expose inference as backend APIs."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Active models" value={overview?.active_models.length ?? 0} tone="info" icon={<BrainCircuit className="h-5 w-5" />} />
        <MetricCard title="Training runs" value={overview?.recent_training_runs.length ?? 0} tone="success" icon={<Workflow className="h-5 w-5" />} />
        <MetricCard
          title="Engagement score"
          value={overview?.latest_feature_snapshot?.user_engagement_score ?? 0}
          tone="warning"
          icon={<Gauge className="h-5 w-5" />}
        />
        <MetricCard
          title="Learning speed"
          value={overview?.latest_feature_snapshot?.learning_speed ?? 0}
          icon={<RefreshCcw className="h-5 w-5" />}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <SurfaceCard
          title="Feature store"
          description="The latest learner feature snapshot that powers model inputs."
          actions={
            <button
              type="button"
              onClick={() => refreshMutation.mutate()}
              className="rounded-2xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white"
            >
              Recompute features
            </button>
          }
        >
          <div className="grid gap-3 md:grid-cols-2">
            {Object.entries(overview?.latest_feature_snapshot ?? {}).map(([key, value]) => (
              <div key={key} className="story-card">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{key.replaceAll("_", " ")}</p>
                <p className="mt-2 text-sm font-semibold text-slate-950">{String(value)}</p>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard title="Training pipeline" description="Trigger retraining and inspect versioned models.">
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => trainRecommendationMutation.mutate()}
              className="rounded-2xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white"
            >
              Train recommendation model
            </button>
            <button
              type="button"
              onClick={() => trainDifficultyMutation.mutate()}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-900"
            >
              Train difficulty model
            </button>
            <button
              type="button"
              onClick={() => trainDropoutMutation.mutate()}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-900"
            >
              Train dropout model
            </button>
          </div>

          <div className="mt-5 space-y-3">
            {(overview?.active_models ?? []).map((model) => (
              <div key={model.id} className="story-card">
                <div className="flex items-center justify-between gap-4">
                  <p className="text-sm font-semibold text-slate-950">{model.model_name}</p>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-700">{model.version}</p>
                </div>
                <p className="mt-2 text-sm text-slate-600">{model.model_type}</p>
                <p className="mt-2 text-sm text-slate-600">{JSON.stringify(model.metrics)}</p>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>

      <SurfaceCard title="Model registry history" description="Recent training runs with dataset volume and metrics.">
        <div className="space-y-3">
          {(overview?.recent_training_runs ?? []).map((run) => (
            <div key={run.id} className="story-card">
              <div className="flex items-center justify-between gap-4">
                <p className="text-sm font-semibold text-slate-950">{run.model_name}</p>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{run.status}</p>
              </div>
              <p className="mt-2 text-sm text-slate-600">Rows trained: {run.trained_rows}</p>
              <p className="mt-2 text-sm text-slate-600">{JSON.stringify(run.metrics)}</p>
            </div>
          ))}
        </div>
      </SurfaceCard>
    </div>
  );
}
