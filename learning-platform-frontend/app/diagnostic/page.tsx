"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, ChevronRight, Loader2 } from "lucide-react";

import RequireAuth from "@/components/auth/RequireAuth";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import SmartLoadingState from "@/components/ui/SmartLoadingState";
import StatusPill from "@/components/ui/StatusPill";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { getGoals } from "@/services/goalService";
import {
  answerDiagnosticQuestion,
  getNextDiagnosticQuestion,
  startDiagnostic,
  submitAnswers,
} from "@/services/diagnosticService";
import type { DiagnosticQuestion, DiagnosticSession } from "@/types/diagnostic";
import type { Goal } from "@/types/goal";

function DiagnosticContent() {
  const router = useRouter();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [selectedGoalId, setSelectedGoalId] = useState<number | null>(null);
  const [session, setSession] = useState<DiagnosticSession | null>(null);
  const [question, setQuestion] = useState<DiagnosticQuestion | null>(null);
  const [answer, setAnswer] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    async function loadGoals() {
      setIsLoading(true);
      setError("");
      try {
        const response = await getGoals();
        setGoals(response.items);
        setSelectedGoalId(response.items[0]?.id ?? null);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Unable to load goals for the diagnostic.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadGoals();
  }, []);

  const canStart = useMemo(() => selectedGoalId !== null && !isSubmitting, [isSubmitting, selectedGoalId]);

  async function handleStart() {
    if (!selectedGoalId) {
      setError("Select a goal before starting the diagnostic.");
      return;
    }

    setIsSubmitting(true);
    setError("");
    setSuccess("");
    try {
      const nextSession = await startDiagnostic(selectedGoalId);
      const nextQuestion = await getNextDiagnosticQuestion(nextSession.id);
      setSession(nextSession);
      setQuestion(nextQuestion);
      setAnswer("");
    } catch (startError) {
      setError(startError instanceof Error ? startError.message : "Unable to start the diagnostic.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleAnswerSubmit() {
    if (!session || !question || !answer.trim()) {
      setError("Enter an answer before continuing.");
      return;
    }

    setIsSubmitting(true);
    setError("");
    try {
      await answerDiagnosticQuestion(session.id, {
        question_id: question.id,
        user_answer: answer.trim(),
        time_taken: 30,
      });
      const nextQuestion = await getNextDiagnosticQuestion(session.id);
      setQuestion(nextQuestion);
      setAnswer("");
      if (!nextQuestion) {
        setSuccess("All questions answered. Submit the diagnostic to generate your roadmap.");
      }
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to save this answer.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleFinish() {
    if (!session) {
      return;
    }

    setIsSubmitting(true);
    setError("");
    try {
      await submitAnswers(session.id);
      router.push("/roadmap");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to submit the diagnostic.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return <SmartLoadingState title="Preparing diagnostic goals" description="We are loading available learning goals before the assessment begins." />;
  }

  return (
    <div className="space-y-6">
      {!session ? (
        <SurfaceCard
          title="Start your diagnostic"
          description="Choose a learning goal and begin the adaptive assessment."
          actions={
            <Button onClick={handleStart} disabled={!canStart}>
              {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              Start diagnostic
            </Button>
          }
        >
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-700 dark:text-slate-200" htmlFor="goal-select">
                Learning goal
              </label>
              <select
                id="goal-select"
                value={selectedGoalId ?? ""}
                onChange={(event) => setSelectedGoalId(Number(event.target.value))}
                className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none ring-0 transition focus:border-teal-400 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              >
                {goals.map((goal) => (
                  <option key={goal.id} value={goal.id}>
                    {goal.name}
                  </option>
                ))}
              </select>
            </div>
            {selectedGoalId ? (
              <p className="text-sm leading-7 text-slate-600 dark:text-slate-300">
                {goals.find((goal) => goal.id === selectedGoalId)?.description ?? "This goal will drive the question set and the roadmap generated afterward."}
              </p>
            ) : null}
          </div>
        </SurfaceCard>
      ) : (
        <SurfaceCard
          title="Diagnostic in progress"
          description={`Test #${session.id} for goal #${session.goal_id}. Answer each question to unlock your roadmap.`}
          actions={question ? <StatusPill label="active" tone="warning" /> : <StatusPill label="ready to submit" tone="success" />}
        >
          {question ? (
            <div className="space-y-5">
              <div className="rounded-[28px] border border-slate-200 bg-white/75 p-5 dark:border-slate-700 dark:bg-slate-900/60">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
                  Topic #{question.topic_id} • {question.difficulty_label}
                </p>
                <h2 className="mt-3 text-2xl font-semibold text-slate-950 dark:text-slate-50">{question.question_text}</h2>

                {question.answer_options.length ? (
                  <div className="mt-5 grid gap-3">
                    {question.answer_options.map((option) => (
                      <button
                        key={option}
                        type="button"
                        onClick={() => setAnswer(option)}
                        className={`rounded-2xl border px-4 py-3 text-left text-sm transition ${
                          answer === option
                            ? "border-teal-400 bg-teal-50 text-teal-900 dark:bg-teal-500/10 dark:text-teal-100"
                            : "border-slate-200 bg-slate-50 text-slate-700 hover:border-slate-300 dark:border-slate-700 dark:bg-slate-950/50 dark:text-slate-200"
                        }`}
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="mt-5">
                    <label className="text-sm font-medium text-slate-700 dark:text-slate-200" htmlFor="diagnostic-answer">
                      Your answer
                    </label>
                    <Input
                      id="diagnostic-answer"
                      value={answer}
                      onChange={(event) => setAnswer(event.target.value)}
                      placeholder="Write your answer here"
                      className="mt-2"
                    />
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-3">
                <Button onClick={handleAnswerSubmit} disabled={isSubmitting || !answer.trim()}>
                  {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <ChevronRight className="h-4 w-4" />}
                  Save answer
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="rounded-[28px] border border-emerald-200 bg-emerald-50/80 p-5 text-emerald-900 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-100">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="h-5 w-5" />
                  <p className="font-semibold">Diagnostic complete</p>
                </div>
                <p className="mt-3 text-sm leading-7">
                  Your answers are recorded. Submit the diagnostic now and Learnova AI will generate or refresh your roadmap.
                </p>
              </div>
              <Button onClick={handleFinish} disabled={isSubmitting}>
                {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                Submit diagnostic
              </Button>
            </div>
          )}
        </SurfaceCard>
      )}

      {error ? <p className="text-sm font-medium text-rose-600">{error}</p> : null}
      {success ? <p className="text-sm font-medium text-emerald-600">{success}</p> : null}
    </div>
  );
}

export default function DiagnosticPage() {
  return (
    <RequireAuth>
      <main className="mx-auto max-w-4xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-teal-700">Diagnostic</p>
          <h1 className="text-4xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">Assess where you are now</h1>
          <p className="max-w-3xl text-base leading-8 text-slate-600 dark:text-slate-300">
            This assessment is powered directly by the backend diagnostic engine. Once you submit it, roadmap generation can continue without leaving the flow.
          </p>
        </header>
        <DiagnosticContent />
      </main>
    </RequireAuth>
  );
}
