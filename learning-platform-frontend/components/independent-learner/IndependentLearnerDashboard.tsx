"use client";

import Link from "next/link";

import type { IndependentLearnerDashboardPayload } from "@/types/dashboard";
import { appRoutes, getLearnerTopicPath } from "@/utils/appRoutes";

type Props = {
  payload: IndependentLearnerDashboardPayload;
};

function formatHours(hours: number) {
  if (hours === 1) {
    return "1 hour";
  }
  return `${hours} hours`;
}

function getResumeBadge(status: string | null | undefined, stepNumber: number | null, topicName: string | null) {
  const stepLabel = stepNumber ? `Step ${stepNumber}` : "Next Step";
  const topicLabel = topicName ? `: ${topicName}` : "";
  const normalized = (status ?? "").toLowerCase();
  if (normalized === "in_progress") {
    return {
      label: `In Progress · ${stepLabel}${topicLabel}`,
      className: "bg-amber-100 text-amber-800 ring-amber-200 hover:bg-amber-200",
    };
  }
  return {
    label: `Resume · ${stepLabel}${topicLabel}`,
    className: "bg-violet-100 text-violet-800 ring-violet-200 hover:bg-violet-200",
  };
}

export default function IndependentLearnerDashboard({ payload }: Props) {
  const nextTopicHref = payload.next_topic?.topic_id
    ? getLearnerTopicPath("independent_learner", payload.next_topic.topic_id)
    : appRoutes.independentLearner.roadmap;
  const nextStep = payload.roadmap_preview[0] ?? null;
  const nextStepStatus = nextStep?.status ?? null;
  const nextStepNumber = nextStep ? 1 : null;
  const resumeBadge = payload.next_topic
    ? getResumeBadge(nextStepStatus, nextStepNumber, nextStep?.topic_name ?? payload.next_topic.topic_name)
    : null;

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(139,92,246,0.22),_transparent_35%),linear-gradient(180deg,_#faf5ff_0%,_#ffffff_52%,_#f5f3ff_100%)] text-slate-900">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <section className="overflow-hidden rounded-3xl border border-violet-200 bg-white/90 p-6 shadow-[0_24px_60px_-30px_rgba(88,28,135,0.45)] backdrop-blur sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-3">
              <div className="space-y-2">
                <h1 className="text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                  Welcome back, {payload.user_name}
                </h1>
                <p className="max-w-2xl text-sm text-slate-600 sm:text-base">
                  {payload.goal ? `You are working toward ${payload.goal}.` : "Choose a goal to begin your roadmap."}
                </p>
              </div>
            </div>
            <div className="flex flex-col gap-4 rounded-2xl bg-violet-600 p-5 text-white shadow-lg shadow-violet-300/60 sm:min-w-72">
              <div>
                <p className="text-sm text-violet-100">Completion</p>
                <p className="text-4xl font-semibold">{Math.round(payload.completion_percent)}%</p>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <Link
                  href={payload.next_topic ? nextTopicHref : appRoutes.independentLearner.goals}
                  className="inline-flex items-center justify-center rounded-xl bg-white px-4 py-3 text-sm font-semibold text-violet-700 transition hover:bg-violet-50"
                >
                  Continue Learning
                </Link>
                {resumeBadge ? (
                  <Link
                    href={nextTopicHref}
                    className={`inline-flex w-fit max-w-full items-center rounded-full px-3 py-1 text-xs font-semibold ring-1 transition ${resumeBadge.className}`}
                    title={resumeBadge.label}
                  >
                    <span className="truncate">{resumeBadge.label}</span>
                  </Link>
                ) : null}
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="grid gap-6 sm:grid-cols-3">
            <article className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">Completion %</p>
              <p className="mt-2 text-3xl font-semibold text-violet-700">{Math.round(payload.completion_percent)}%</p>
            </article>
            <article className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">Completed Topics</p>
              <p className="mt-2 text-3xl font-semibold text-slate-900">{payload.completed_topics}</p>
            </article>
            <article className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">Remaining Topics</p>
              <p className="mt-2 text-3xl font-semibold text-slate-900">{payload.remaining_topics}</p>
            </article>
          </div>

          <article className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-violet-600">Next Action</p>
            {payload.next_topic ? (
              <div className="mt-4 space-y-4">
                <div>
                  <h2 className="text-2xl font-semibold text-slate-950">{payload.next_topic.topic_name}</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{payload.next_topic.reason}</p>
                </div>
                <p className="text-sm text-slate-500">
                  Estimated time: <span className="font-medium text-slate-900">{formatHours(payload.next_topic.estimated_time_hours)}</span>
                </p>
                <Link
                  href={nextTopicHref}
                  className="inline-flex items-center justify-center rounded-xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-violet-700"
                >
                  Open Topic
                </Link>
              </div>
            ) : (
              <div className="mt-4 rounded-xl bg-violet-50 p-4 text-sm text-slate-600">
                Your next learning action will appear here after roadmap generation.
              </div>
            )}
          </article>
        </section>

        <section className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
          <article className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-violet-600">Weak Topics</p>
            {payload.weak_topics.length > 0 ? (
              <ul className="mt-4 space-y-3">
                {payload.weak_topics.map((topic) => (
                  <li key={topic} className="rounded-xl bg-violet-50 px-4 py-3 text-sm font-medium text-slate-800">
                    {topic}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-4 text-sm text-slate-600">No weak topics detected yet. Complete a diagnostic to personalize this list.</p>
            )}
          </article>

          <article className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm">
            <div>
              <p className="text-sm font-medium text-violet-600">Roadmap Preview</p>
              <h2 className="mt-1 text-xl font-semibold text-slate-950">Your next steps</h2>
            </div>
            {payload.roadmap_preview.length > 0 ? (
              <div className="mt-4 space-y-3">
                {payload.roadmap_preview.map((step, index) => (
                  <Link
                    key={step.step_id}
                    href={getLearnerTopicPath("independent_learner", step.topic_id)}
                    className="flex flex-col gap-3 rounded-2xl border border-violet-100 bg-violet-50/60 p-4 transition hover:bg-violet-100/80 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="space-y-1">
                      <p className="text-xs font-medium uppercase tracking-[0.18em] text-violet-500">Step {index + 1}</p>
                      <h3 className="text-base font-semibold text-slate-900">{step.topic_name}</h3>
                      <p className="text-sm text-slate-500">
                        {step.difficulty} difficulty • {formatHours(step.estimated_time_hours)}
                      </p>
                    </div>
                    <span className="inline-flex w-fit rounded-full bg-white px-3 py-1 text-xs font-semibold capitalize text-violet-700 ring-1 ring-violet-200">
                      {step.status.replaceAll("_", " ")}
                    </span>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="mt-4 text-sm text-slate-600">Your roadmap preview will appear once your learning path is ready.</p>
            )}
          </article>
        </section>
      </div>
    </div>
  );
}
