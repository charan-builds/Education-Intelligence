"use client";

import Link from "next/link";
import { Compass, Play, Sparkles } from "lucide-react";
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
              <MetricCard title="Answered" value={answers.length} tone="success" />
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
          >
            <p className="text-base font-semibold text-slate-950 dark:text-slate-100">{currentQuestion.question_text}</p>

            {currentQuestion.question_type === "multiple_choice" && currentQuestion.answer_options.length > 0 ? (
              <div className="mt-6 grid gap-3">
                {currentQuestion.answer_options.map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setAnswerValue(option)}
                    className={[
                      "rounded-2xl border px-4 py-3 text-left text-sm font-medium transition",
                      answerValue === option
                        ? "border-sky-500 bg-sky-50 text-sky-900"
                        : "border-slate-200 bg-white hover:border-slate-300",
                    ].join(" ")}
                  >
                    {option}
                  </button>
                ))}
              </div>
            ) : (
              <textarea
                value={answerValue}
                onChange={(event) => setAnswerValue(event.target.value)}
                className="mt-6 min-h-36 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-sky-400"
                placeholder="Type your answer here"
              />
            )}

            <div className="mt-6 flex flex-wrap gap-3">
              <Button onClick={() => void handleAnswerSubmit()} disabled={!answerValue.trim() || nextQuestionMutation.isPending || submitMutation.isPending}>
                {submitMutation.isPending ? "Submitting..." : nextQuestionMutation.isPending ? "Loading..." : "Continue"}
              </Button>
              <Link href={learnerRoutes.goals} className="inline-flex items-center rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                Exit diagnostic
              </Link>
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

        <SurfaceCard title="Goal library" description="Start a diagnostic directly from any goal returned by the backend.">
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
                  className="rounded-[28px] border border-slate-200 bg-white/75 p-5 dark:border-slate-700 dark:bg-slate-900/75"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-950 dark:text-slate-100">{goal.name}</p>
                      <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-400">{goal.description}</p>
                    </div>
                    <Button
                      onClick={() => startMutation.mutate(goal.id)}
                      disabled={startMutation.isPending}
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
