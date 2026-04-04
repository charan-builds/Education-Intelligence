"use client";

import Link from "next/link";
import { CheckCircle2, Compass, Play, Sparkles, TimerReset } from "lucide-react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import PageHeader from "@/components/layouts/PageHeader";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorState from "@/components/ui/ErrorState";
import MetricCard from "@/components/ui/MetricCard";
import Skeleton from "@/components/ui/Skeleton";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useToast } from "@/components/providers/ToastProvider";
import { answerDiagnosticQuestion, getDiagnosticSession, getNextDiagnosticQuestion, startDiagnostic, submitAnswers } from "@/services/diagnosticService";
import { getGoals } from "@/services/goalService";
import { useAuth } from "@/hooks/useAuth";
import type { DiagnosticAnswerPayload, DiagnosticQuestion } from "@/types/diagnostic";
import { getLearnerRoutes } from "@/utils/appRoutes";

function getOptionBadge(index: number) {
  return String.fromCharCode(65 + index);
}

export default function StudentDiagnosticPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { role } = useAuth();
  const learnerRoutes = getLearnerRoutes(role);
  const { toast } = useToast();
  const testId = Number(searchParams.get("test_id") ?? "");
  const goalIdFromQuery = Number(searchParams.get("goal_id") ?? "");
  const isTestMode = Number.isFinite(testId) && testId > 0 && Number.isFinite(goalIdFromQuery) && goalIdFromQuery > 0;
  const [currentQuestion, setCurrentQuestion] = useState<DiagnosticQuestion | null>(null);
  const [answers, setAnswers] = useState<DiagnosticAnswerPayload[]>([]);
  const [answerValue, setAnswerValue] = useState("");
  const [questionStartedAt, setQuestionStartedAt] = useState<number>(Date.now());
  const [flowError, setFlowError] = useState<string | null>(null);
  const answeredCount = answers.length;
  const visibleStep = answeredCount + (currentQuestion ? 1 : 0);
  const progressWidth = Math.min(100, Math.max(14, visibleStep * 14));

  const goalsQuery = useQuery({
    queryKey: ["student", "diagnostic", "goals"],
    queryFn: getGoals,
    enabled: !isTestMode,
  });

  const startMutation = useMutation({
    mutationFn: startDiagnostic,
    onSuccess: (session, goalId) => {
      toast({
        title: "Diagnostic started",
        description: `Opening adaptive diagnostic for goal ${goalId}.`,
        variant: "success",
      });
      router.push(`${learnerRoutes.diagnostic}?goal_id=${goalId}&test_id=${session.id}`);
    },
    onError: () => {
      toast({
        title: "Diagnostic could not start",
        description: "The backend rejected the start request. Check your session and tenant context.",
        variant: "error",
      });
    },
  });

  const nextQuestionMutation = useMutation({
    mutationFn: (payload: { testId: number }) => getNextDiagnosticQuestion(payload.testId),
    onSuccess: (question) => {
      if (question === null) {
        router.replace(`${learnerRoutes.diagnosticResult}?test_id=${testId}`);
        return;
      }
      setCurrentQuestion(question);
      setQuestionStartedAt(Date.now());
    },
    onError: () => {
      setFlowError("Unable to load the next diagnostic question.");
    },
  });
  const loadNextQuestion = nextQuestionMutation.mutateAsync;

  const submitMutation = useMutation({
    mutationFn: (payload: { testId: number }) => submitAnswers(payload.testId),
    onSuccess: (session) => {
      toast({
        title: "Diagnostic complete",
        description: "Your answers were submitted successfully.",
        variant: "success",
      });
      router.replace(`${learnerRoutes.diagnosticResult}?test_id=${session.id}`);
    },
    onError: () => {
      setFlowError("Unable to submit the diagnostic answers.");
    },
  });

  useEffect(() => {
    if (!isTestMode) {
      setCurrentQuestion(null);
      setAnswers([]);
      setAnswerValue("");
      setFlowError(null);
      return;
    }
    setFlowError(null);
    setAnswers([]);
    setAnswerValue("");
    void getDiagnosticSession(testId)
      .then((session) => {
        const answeredCount = session.answered_count ?? 0;
        if (session.completed_at) {
          router.replace(`${learnerRoutes.diagnosticResult}?test_id=${session.id}`);
          return null;
        }
        if (answeredCount > 0) {
          setAnswers(Array.from({ length: answeredCount }).map((_, index) => ({
            question_id: -(index + 1),
            user_answer: "",
            time_taken: 0,
          })));
        }
        return loadNextQuestion({ testId });
      })
      .catch(() => setFlowError("Unable to resume the diagnostic session."));
  }, [isTestMode, learnerRoutes.diagnosticResult, loadNextQuestion, router, testId]);

  const goals = goalsQuery.data?.items ?? [];

  async function handleAnswerSubmit() {
    if (!currentQuestion || !answerValue.trim()) {
      return;
    }

    const answerPayload = {
      question_id: currentQuestion.id,
      user_answer: answerValue.trim(),
      time_taken: Math.max(1, Math.round((Date.now() - questionStartedAt) / 1000)),
    };

    setAnswerValue("");
    setFlowError(null);
    await answerDiagnosticQuestion(testId, answerPayload);
    const nextAnswers = [...answers, answerPayload];
    setAnswers(nextAnswers);

    const nextQuestion = await loadNextQuestion({ testId });

    if (nextQuestion === null) {
      await submitMutation.mutateAsync({ testId });
    }
  }

  if (isTestMode) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Diagnostic"
          title="Complete your adaptive diagnostic"
          description="Answer the current question and the platform will choose the next one using the backend adaptive testing endpoint."
          meta={
            <>
              <MetricCard title="Goal" value={goalIdFromQuery} tone="info" />
              <MetricCard title="Answered" value={answeredCount} tone="success" />
            </>
          }
        />

        {nextQuestionMutation.isPending && !currentQuestion ? (
          <div className="space-y-4">
            <Skeleton className="h-36 w-full" />
            <Skeleton className="h-52 w-full" />
          </div>
        ) : null}

        {flowError ? <ErrorState description={flowError} onRetry={() => void loadNextQuestion({ testId })} /> : null}

        {!nextQuestionMutation.isPending && !flowError && currentQuestion ? (
          <SurfaceCard
            title={`Question ${answers.length + 1}`}
            description={`Difficulty: ${currentQuestion.difficulty_label}. Answer and continue to the next adaptive step.`}
            className="overflow-hidden bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.16),_transparent_42%),linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.96))] dark:bg-[radial-gradient(circle_at_top_left,_rgba(96,165,250,0.16),_transparent_42%),linear-gradient(180deg,rgba(15,23,42,0.98),rgba(2,6,23,0.98))]"
          >
            <div className="space-y-6">
              <div className="rounded-[28px] border border-sky-100 bg-white/90 p-5 shadow-[0_18px_45px_-28px_rgba(14,165,233,0.45)] dark:border-sky-400/20 dark:bg-slate-950/70">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div className="space-y-3">
                    <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-sky-700 dark:border-sky-400/20 dark:bg-sky-500/10 dark:text-sky-200">
                      Adaptive step {visibleStep}
                    </div>
                    <div className="max-w-3xl">
                      <p className="text-lg font-semibold leading-8 text-slate-950 dark:text-slate-50">{currentQuestion.question_text}</p>
                    </div>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[260px]">
                    <div className="rounded-2xl border border-emerald-200 bg-emerald-50/90 px-4 py-3 dark:border-emerald-400/20 dark:bg-emerald-500/10">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-emerald-700 dark:text-emerald-200">Difficulty</p>
                      <p className="mt-1 text-sm font-semibold text-emerald-950 dark:text-emerald-50">{currentQuestion.difficulty_label}</p>
                    </div>
                    <div className="rounded-2xl border border-amber-200 bg-amber-50/90 px-4 py-3 dark:border-amber-400/20 dark:bg-amber-500/10">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-amber-700 dark:text-amber-200">Pace</p>
                      <p className="mt-1 flex items-center gap-2 text-sm font-semibold text-amber-950 dark:text-amber-50">
                        <TimerReset className="h-4 w-4" />
                        Answer thoughtfully
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mt-5">
                  <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                    <span>Progress</span>
                    <span>{answeredCount} completed</span>
                  </div>
                  <div className="mt-2 h-3 rounded-full bg-slate-200/80 dark:bg-slate-800">
                    <div
                      className="h-3 rounded-full bg-gradient-to-r from-sky-500 via-cyan-500 to-emerald-500 transition-all duration-500"
                      style={{ width: `${progressWidth}%` }}
                    />
                  </div>
                </div>
              </div>

              {currentQuestion.question_type === "multiple_choice" && currentQuestion.answer_options.length > 0 ? (
                <div className="grid gap-4">
                  {currentQuestion.answer_options.map((option, index) => {
                    const isSelected = answerValue === option;
                    return (
                      <button
                        key={option}
                        type="button"
                        onClick={() => setAnswerValue(option)}
                        className={[
                          "group rounded-[26px] border px-5 py-4 text-left transition duration-200",
                          isSelected
                            ? "border-sky-500 bg-gradient-to-r from-sky-50 to-cyan-50 shadow-[0_18px_45px_-28px_rgba(14,165,233,0.55)] dark:border-sky-400 dark:bg-sky-500/10"
                            : "border-slate-200 bg-white/90 hover:-translate-y-0.5 hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-950/70 dark:hover:border-slate-500 dark:hover:bg-slate-900",
                        ].join(" ")}
                      >
                        <div className="flex items-start gap-4">
                          <div
                            className={[
                              "flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border text-sm font-bold transition",
                              isSelected
                                ? "border-sky-500 bg-sky-500 text-white"
                                : "border-slate-300 bg-slate-50 text-slate-700 group-hover:border-slate-400 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-200",
                            ].join(" ")}
                          >
                            {getOptionBadge(index)}
                          </div>
                          <div className="flex-1">
                            <p className="text-sm font-semibold text-slate-950 dark:text-slate-50">{option}</p>
                            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                              {isSelected ? "Selected answer" : "Tap to choose this answer"}
                            </p>
                          </div>
                          {isSelected ? <CheckCircle2 className="mt-0.5 h-5 w-5 text-sky-600 dark:text-sky-300" /> : null}
                        </div>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="rounded-[28px] border border-slate-200 bg-white/90 p-4 shadow-[0_16px_40px_-30px_rgba(15,23,42,0.35)] dark:border-slate-700 dark:bg-slate-950/70">
                  <div className="mb-3 flex items-center justify-between">
                    <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Write your response</p>
                    <p className="text-xs font-medium text-slate-500 dark:text-slate-400">Clear and concise is best</p>
                  </div>
                  <textarea
                    value={answerValue}
                    onChange={(event) => setAnswerValue(event.target.value)}
                    className="min-h-40 w-full rounded-[24px] border border-slate-200 bg-slate-50/85 px-4 py-3 text-sm leading-7 text-slate-900 outline-none transition focus:border-sky-400 focus:bg-white focus:ring-4 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-sky-400 dark:focus:bg-slate-950 dark:focus:ring-sky-500/10"
                    placeholder="Type your answer here"
                  />
                </div>
              )}

              <div className="flex flex-wrap items-center justify-between gap-4 rounded-[26px] border border-slate-200/80 bg-white/80 px-4 py-4 dark:border-slate-700 dark:bg-slate-950/65">
                <div>
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Ready for the next step?</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Your answer is submitted immediately and the next question adapts to your response.
                  </p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <Button
                    onClick={() => void handleAnswerSubmit()}
                    disabled={!answerValue.trim() || nextQuestionMutation.isPending || submitMutation.isPending}
                    className="min-w-[148px]"
                  >
                    {submitMutation.isPending ? "Submitting..." : nextQuestionMutation.isPending ? "Loading..." : "Continue"}
                  </Button>
                  <Link
                    href={learnerRoutes.goals}
                    className="inline-flex items-center rounded-2xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-900"
                  >
                    Exit diagnostic
                  </Link>
                </div>
              </div>
            </div>
          </SurfaceCard>
        ) : null}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Diagnostic"
        title="Launch an adaptive knowledge check"
        description="Choose a learning goal and start the diagnostic flow backed by `/diagnostic/start` and `/diagnostic/next-question`."
        meta={
          <>
            <MetricCard title="Available goals" value={goals.length} tone="info" />
            <MetricCard title="Adaptive engine" value="Active" tone="success" />
          </>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <SurfaceCard
          title="How it works"
          description="The backend creates a diagnostic session, serves adaptive questions, and scores the result for roadmap generation."
          className="bg-[radial-gradient(circle_at_top_right,_rgba(34,197,94,0.14),_transparent_38%),linear-gradient(180deg,rgba(255,255,255,0.96),rgba(248,250,252,0.94))] dark:bg-[radial-gradient(circle_at_top_right,_rgba(34,197,94,0.12),_transparent_38%),linear-gradient(180deg,rgba(15,23,42,0.98),rgba(2,6,23,0.98))]"
        >
          <div className="grid gap-3">
            {[
              "Select a goal aligned to your current learning target.",
              "Start the diagnostic session and answer adaptive questions.",
              "Use the result to generate a personalized roadmap.",
            ].map((step, index) => (
              <div
                key={step}
                className="flex gap-3 rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-100 text-brand-700 dark:bg-brand-900/50 dark:text-brand-100">
                  {index + 1}
                </div>
                <p className="text-sm leading-7 text-slate-700 dark:text-slate-300">{step}</p>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard
          title="Goal library"
          description="Start a diagnostic directly from any goal returned by the backend."
          className="bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.16),_transparent_42%),linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.95))] dark:bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.12),_transparent_42%),linear-gradient(180deg,rgba(15,23,42,0.98),rgba(2,6,23,0.98))]"
        >
          {goalsQuery.isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} className="h-28 w-full" />
              ))}
            </div>
          ) : goalsQuery.isError ? (
            <ErrorState description="Goal loading failed. Verify the goals API is reachable." onRetry={() => void goalsQuery.refetch()} />
          ) : goals.length === 0 ? (
            <EmptyState
              title="No goals available"
              description="An admin needs to create at least one goal before a diagnostic can begin."
            />
          ) : (
            <div className="space-y-3">
              {goals.map((goal) => (
                <div
                  key={goal.id}
                  className="rounded-[28px] border border-slate-200 bg-white/85 p-5 shadow-[0_18px_45px_-30px_rgba(15,23,42,0.28)] transition hover:-translate-y-0.5 hover:border-sky-300 dark:border-slate-700 dark:bg-slate-900/75 dark:hover:border-sky-400/40"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                      <div className="inline-flex items-center rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-700 dark:border-sky-400/20 dark:bg-sky-500/10 dark:text-sky-200">
                        Goal {goal.id}
                      </div>
                      <p className="mt-3 text-base font-semibold text-slate-950 dark:text-slate-100">{goal.name}</p>
                      <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-400">{goal.description}</p>
                    </div>
                    <Button
                      onClick={() => startMutation.mutate(goal.id)}
                      disabled={startMutation.isPending}
                      className="min-w-[132px]"
                    >
                      <Play className="h-4 w-4" />
                      Start
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
          <div className="mt-5 flex flex-wrap gap-3">
            <Link href={learnerRoutes.dashboard} className="inline-flex items-center gap-2 text-sm font-semibold text-brand-700 dark:text-brand-200">
              <Compass className="h-4 w-4" />
              Back to dashboard
            </Link>
            <Link href={learnerRoutes.roadmap} className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 dark:text-slate-300">
              <Sparkles className="h-4 w-4" />
              See roadmap area
            </Link>
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}
