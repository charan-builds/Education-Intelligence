"use client";

import { useQuery } from "@tanstack/react-query";
import { BrainCircuit, Gauge, Orbit, Sparkles } from "lucide-react";

import ProgressLineChart from "@/components/charts/ProgressLineChart";
import PageHeader from "@/components/layouts/PageHeader";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { getDigitalTwin } from "@/services/digitalTwinService";

export default function StudentDigitalTwinPage() {
  const twinQuery = useQuery({
    queryKey: ["student", "digital-twin"],
    queryFn: getDigitalTwin,
  });

  const twin = twinQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Digital twin"
        title="A simulated model of how you learn"
        description="This workspace turns your learning behavior into a virtual twin that models strengths, weaknesses, retention, future outcomes, and the best strategy to follow next."
      />

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Twin confidence" value={`${Math.round(twin?.current_model.twin_confidence ?? 0)}%`} tone="info" icon={<Orbit className="h-5 w-5" />} />
        <MetricCard title="Learning speed" value={Math.round(twin?.current_model.learning_speed ?? 0)} tone="success" icon={<Gauge className="h-5 w-5" />} />
        <MetricCard title="Retention" value={`${Math.round(twin?.current_model.memory_retention ?? 0)}%`} tone="warning" icon={<BrainCircuit className="h-5 w-5" />} />
        <MetricCard title="Risk level" value={twin?.predictions.risk_prediction.risk_level ?? "unknown"} icon={<Sparkles className="h-5 w-5" />} />
      </div>

      <SurfaceCard
        title="Twin summary"
        description="The system is estimating how you learn, where you are strongest, and what will likely happen next."
        className="premium-hero"
      >
        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="story-card">
            <p className="text-sm leading-7 text-slate-700">{twin?.current_model.learner_summary ?? "Building learner twin..."}</p>
          </div>
          <div className="story-card">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Recommended strategy</p>
            <p className="mt-3 text-2xl font-semibold text-slate-950">
              {twin?.decision_support.recommended_strategy.strategy.replaceAll("_", " ") ?? "Loading"}
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-600">{twin?.decision_support.recommended_strategy.summary ?? "Simulating strategy options."}</p>
          </div>
        </div>
      </SurfaceCard>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SurfaceCard title="Strength map" description="Topics the twin believes you can compound from immediately.">
          <div className="grid gap-3 md:grid-cols-2">
            {(twin?.current_model.strengths ?? []).map((item) => (
              <div key={item.topic_id} className="rounded-[24px] border border-emerald-200 bg-emerald-50/85 px-4 py-3">
                <p className="text-sm font-semibold text-emerald-950">{item.topic_name}</p>
                <p className="mt-2 text-xs uppercase tracking-[0.2em] text-emerald-700">{Math.round(item.score)}% mastery</p>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard title="Weakness map" description="Topics that are suppressing future performance if left unresolved.">
          <div className="grid gap-3 md:grid-cols-2">
            {(twin?.current_model.weaknesses ?? []).map((item) => (
              <div key={item.topic_id} className="rounded-[24px] border border-rose-200 bg-rose-50/85 px-4 py-3">
                <p className="text-sm font-semibold text-rose-950">{item.topic_name}</p>
                <p className="mt-2 text-xs uppercase tracking-[0.2em] text-rose-700">
                  {Math.round(item.score)}% mastery • {Math.round(item.retention_score ?? 0)}% retention
                </p>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <ProgressLineChart
          title="Baseline simulation"
          description="Predicted roadmap progress if you continue at your current modeled pace."
          data={(twin?.predictions.baseline.progress_curve ?? []).map((point) => ({
            label: `D${point.day}`,
            progress: point.progress_percent,
          }))}
        />
        <SurfaceCard title="Behavior model" description="Patterns the twin detects from activity, pace, and consistency.">
          <div className="space-y-3">
            <div className="story-card">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Cadence pattern</p>
              <p className="mt-3 text-xl font-semibold text-slate-950">{twin?.current_model.behavior_patterns.cadence_pattern ?? "..."}</p>
            </div>
            <div className="story-card">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Profile type</p>
              <p className="mt-3 text-xl font-semibold text-slate-950">{twin?.current_model.behavior_patterns.profile_type ?? "..."}</p>
            </div>
            <div className="story-card">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Consistency</p>
              <p className="mt-3 text-xl font-semibold text-slate-950">{Math.round(twin?.current_model.behavior_patterns.consistency ?? 0)}%</p>
            </div>
          </div>
        </SurfaceCard>
      </div>

      <SurfaceCard title="Strategy simulation" description="Compare how different learning strategies affect speed, readiness, and retention.">
        <div className="grid gap-4 md:grid-cols-3">
          {(twin?.decision_support.strategy_comparison ?? []).map((strategy) => (
            <div key={strategy.strategy} className="story-card">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">{strategy.strategy.replaceAll("_", " ")}</p>
              <p className="mt-3 text-xl font-semibold text-slate-950">{strategy.predicted_readiness_percent}% readiness</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">{strategy.tradeoff}</p>
              <p className="mt-3 text-xs uppercase tracking-[0.2em] text-slate-400">Finish by {strategy.predicted_completion_date}</p>
            </div>
          ))}
        </div>
      </SurfaceCard>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SurfaceCard title="Recommended path" description="What the twin believes you should learn next, in order.">
          <div className="space-y-3">
            {(twin?.decision_support.recommended_learning_path ?? []).map((item, index) => (
              <div key={`${item}-${index}`} className="rounded-[24px] border border-white/70 bg-white/80 px-4 py-3">
                <p className="text-sm font-semibold text-slate-950">{index + 1}. {item}</p>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard title="Why the twin chose this" description="The reasoning layer behind the recommendation.">
          <div className="space-y-3">
            {(twin?.decision_support.why ?? []).map((item, index) => (
              <div key={`${item}-${index}`} className="rounded-[24px] border border-sky-200 bg-sky-50/85 px-4 py-3">
                <p className="text-sm leading-7 text-sky-950">{item}</p>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}
