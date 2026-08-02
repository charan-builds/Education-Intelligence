"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import Button from "@/components/ui/Button";
import QuestionCard from "@/components/diagnostic/QuestionCard";
import TimerComponent from "@/components/diagnostic/TimerComponent";
import WarningModal from "@/components/diagnostic/WarningModal";
import { useToast } from "@/components/providers/ToastProvider";
import { useDiagnosticCountdown } from "@/hooks/useDiagnosticCountdown";
import { DIAGNOSTIC_DURATION_SECONDS, DIAGNOSTIC_TOTAL_QUESTIONS } from "@/features/diagnostic/config";
import { answerDiagnosticQuestion, getNextDiagnosticQuestion, submitAnswers } from "@/services/diagnosticService";
import { useDiagnosticTestStore } from "@/stores/useDiagnosticTestStore";
import type { DiagnosticQuestion, DiagnosticSession, DiagnosticSubmitAnswerPayload } from "@/types/diagnostic";
import { getLearnerRoutes } from "@/utils/appRoutes";

type Props = {
  session: DiagnosticSession;
  initialQuestion: DiagnosticQuestion | null;
  role: string | null | undefined;
};

const BLOCKED_SHORTCUTS = new Set(["c", "v", "x", "a", "p", "s", "u", "r"]);

export default function TestScreen({ session, initialQuestion, role }: Props) {
  const router = useRouter();
  const { toast } = useToast();
  const learnerRoutes = getLearnerRoutes(role);
  const initialQuestionBank = useMemo(
    () => (session.questions?.length ? session.questions : initialQuestion ? [initialQuestion] : []),
    [initialQuestion, session.questions],
  );
  const [questionBank, setQuestionBank] = useState<DiagnosticQuestion[]>(initialQuestionBank);
  const [currentQuestion, setCurrentQuestion] = useState<DiagnosticQuestion | null>(initialQuestionBank[0] ?? null);
  const [answersByQuestionId, setAnswersByQuestionId] = useState<Record<number, string>>({});
  const [answerStartedAtByQuestionId, setAnswerStartedAtByQuestionId] = useState<Record<number, number>>({});
  const [timeTakenByQuestionId, setTimeTakenByQuestionId] = useState<Record<number, number>>({});
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [questionStartedAt, setQuestionStartedAt] = useState(Date.now());
  const [fullscreenLocked, setFullscreenLocked] = useState(false);
  const [autoSubmittingReason, setAutoSubmittingReason] = useState<string | null>(null);
  const submittedRef = useRef(false);
  const warning = useDiagnosticTestStore((state) => state.latestWarning);
  const clearWarning = useDiagnosticTestStore((state) => state.clearWarning);
  const registerTabWarning = useDiagnosticTestStore((state) => state.registerTabWarning);
  const setWarning = useDiagnosticTestStore((state) => state.setWarning);
  const currentQuestionIndex = useDiagnosticTestStore((state) => state.currentQuestionIndex);
  const setQuestionIndex = useDiagnosticTestStore((state) => state.setQuestionIndex);

  const totalQuestions = questionBank.length || DIAGNOSTIC_TOTAL_QUESTIONS;
  const activeQuestionIndex = useMemo(
    () => Math.max(0, questionBank.findIndex((question) => question.id === currentQuestion?.id)),
    [currentQuestion?.id, questionBank],
  );
  const visibleQuestionIndex = Math.min(totalQuestions, activeQuestionIndex + 1 || currentQuestionIndex);
  const selectedAnswer = currentQuestion ? answersByQuestionId[currentQuestion.id] ?? "" : "";
  const answeredCount = useMemo(
    () => questionBank.filter((question) => Boolean((answersByQuestionId[question.id] ?? "").trim())).length,
    [answersByQuestionId, questionBank],
  );
  const progressPercent = Math.min(100, Math.round((answeredCount / Math.max(totalQuestions, 1)) * 100));
  const storageKey = `diagnostic-draft:${session.id}`;

  const submitMutation = useMutation({
    mutationFn: (answers?: DiagnosticSubmitAnswerPayload[]) => submitAnswers(session.id, answers),
  });

  const submitTest = useCallback(
    async (reason: string) => {
      if (submittedRef.current) {
        return;
      }
      submittedRef.current = true;
      setAutoSubmittingReason(reason);
      try {
        const answers = questionBank
          .map((question): DiagnosticSubmitAnswerPayload | null => {
            const selected = (answersByQuestionId[question.id] ?? "").trim();
            if (!selected) {
              return null;
            }
            return {
              question_id: question.id,
              selected_answer: selected,
              time_taken: Math.max(
                1,
                timeTakenByQuestionId[question.id] ?? Math.round((Date.now() - (answerStartedAtByQuestionId[question.id] ?? questionStartedAt)) / 1000),
              ),
            };
          })
          .filter((answer): answer is DiagnosticSubmitAnswerPayload => Boolean(answer));
        await submitMutation.mutateAsync(answers);
        window.localStorage.removeItem(storageKey);
        toast({
          title: "Diagnostic submitted",
          description: reason,
          variant: "success",
        });
      } catch {
        toast({
          title: "Submission failed",
          description: "The diagnostic could not be submitted cleanly.",
          variant: "error",
        });
      } finally {
        router.replace(`${learnerRoutes.diagnosticResult}?test_id=${session.id}`);
      }
    },
    [
      answerStartedAtByQuestionId,
      answersByQuestionId,
      learnerRoutes.diagnosticResult,
      questionBank,
      questionStartedAt,
      router,
      session.id,
      storageKey,
      submitMutation,
      timeTakenByQuestionId,
      toast,
    ],
  );

  const remainingSeconds = useDiagnosticCountdown({
    startedAtIso: session.started_at,
    totalSeconds: DIAGNOSTIC_DURATION_SECONDS,
    enabled: !submittedRef.current,
    onExpire: () => {
      void submitTest("Time expired. The diagnostic was auto-submitted.");
    },
  });

  useEffect(() => {
    if (initialQuestionBank.length) {
      setQuestionBank(initialQuestionBank);
      setCurrentQuestion((current) => current ?? initialQuestionBank[0] ?? null);
    }
  }, [initialQuestionBank]);

  useEffect(() => {
    try {
      const rawDraft = window.localStorage.getItem(storageKey);
      if (!rawDraft) {
        return;
      }
      const draft = JSON.parse(rawDraft) as {
        answersByQuestionId?: Record<string, string>;
        timeTakenByQuestionId?: Record<string, number>;
      };
      setAnswersByQuestionId(
        Object.fromEntries(
          Object.entries(draft.answersByQuestionId ?? {}).map(([questionId, value]) => [Number(questionId), String(value)]),
        ),
      );
      setTimeTakenByQuestionId(
        Object.fromEntries(
          Object.entries(draft.timeTakenByQuestionId ?? {}).map(([questionId, value]) => [Number(questionId), Number(value)]),
        ),
      );
      setLastSavedAt(new Date());
    } catch {
      window.localStorage.removeItem(storageKey);
    }
  }, [storageKey]);

  useEffect(() => {
    const saveTimer = window.setTimeout(() => {
      window.localStorage.setItem(
        storageKey,
        JSON.stringify({
          answersByQuestionId,
          timeTakenByQuestionId,
          savedAt: new Date().toISOString(),
        }),
      );
      setLastSavedAt(new Date());
    }, 500);

    return () => window.clearTimeout(saveTimer);
  }, [answersByQuestionId, storageKey, timeTakenByQuestionId]);

  useEffect(() => {
    if (!currentQuestion) {
      return;
    }
    setAnswerStartedAtByQuestionId((current) => ({
      ...current,
      [currentQuestion.id]: current[currentQuestion.id] ?? Date.now(),
    }));
  }, [currentQuestion]);

  const requestFullscreen = useCallback(async () => {
    if (document.fullscreenElement) {
      setFullscreenLocked(false);
      clearWarning();
      return;
    }
    await document.documentElement.requestFullscreen();
    setFullscreenLocked(false);
    clearWarning();
  }, [clearWarning]);

  useEffect(() => {
    void requestFullscreen().catch(() => {
      setFullscreenLocked(true);
      setWarning({
        title: "Fullscreen required",
        description: "Enter fullscreen to continue the diagnostic. Exiting fullscreen interrupts the test flow.",
        blocking: true,
      });
    });
  }, [requestFullscreen, setWarning]);

  useEffect(() => {
    const registerFocusWarning = () => {
      const warningCount = registerTabWarning({
        title: "Focus change detected",
        description: "Leaving the diagnostic window is blocked. Repeated focus changes will auto-submit the test.",
      });
      if (warningCount > 2) {
        void submitTest("The test was auto-submitted after repeated focus changes.");
      }
    };

    const onVisibilityChange = () => {
      if (document.hidden) {
        registerFocusWarning();
      }
    };

    const preventBrowserAction = (event: Event) => {
      event.preventDefault();
    };

    const onKeyDown = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      if (event.key === "F5" || ((event.ctrlKey || event.metaKey) && BLOCKED_SHORTCUTS.has(key))) {
        event.preventDefault();
        setWarning({
          title: "Shortcut blocked",
          description: "Copy, paste, refresh, and similar shortcuts are disabled during the diagnostic.",
        });
      }
    };

    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };

    const onFullscreenChange = () => {
      if (!document.fullscreenElement) {
        setFullscreenLocked(true);
        setWarning({
          title: "Fullscreen exited",
          description: "You must return to fullscreen to continue. The diagnostic remains locked until you do.",
          blocking: true,
        });
      }
    };

    document.addEventListener("visibilitychange", onVisibilityChange);
    document.addEventListener("copy", preventBrowserAction);
    document.addEventListener("paste", preventBrowserAction);
    document.addEventListener("cut", preventBrowserAction);
    document.addEventListener("contextmenu", preventBrowserAction);
    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("fullscreenchange", onFullscreenChange);
    window.addEventListener("blur", registerFocusWarning);
    window.addEventListener("beforeunload", onBeforeUnload);

    return () => {
      document.removeEventListener("visibilitychange", onVisibilityChange);
      document.removeEventListener("copy", preventBrowserAction);
      document.removeEventListener("paste", preventBrowserAction);
      document.removeEventListener("cut", preventBrowserAction);
      document.removeEventListener("contextmenu", preventBrowserAction);
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("fullscreenchange", onFullscreenChange);
      window.removeEventListener("blur", registerFocusWarning);
      window.removeEventListener("beforeunload", onBeforeUnload);
    };
  }, [registerTabWarning, setWarning, submitTest]);

  const handleAdvance = useCallback(async () => {
    if (!currentQuestion || !selectedAnswer || submittedRef.current) {
      return;
    }

    if (questionBank.length > 1) {
      const nextQuestion = questionBank[activeQuestionIndex + 1];
      if (!nextQuestion) {
        await submitTest("The diagnostic was submitted after the final question.");
        return;
      }
      setCurrentQuestion(nextQuestion);
      setQuestionIndex(activeQuestionIndex + 2);
      setQuestionStartedAt(Date.now());
      return;
    }

    const answerPayload = {
      question_id: currentQuestion.id,
      user_answer: selectedAnswer,
      time_taken: Math.max(1, Math.round((Date.now() - questionStartedAt) / 1000)),
    };

    try {
      await answerDiagnosticQuestion(session.id, answerPayload);
      const nextIndex = visibleQuestionIndex + 1;

      if (visibleQuestionIndex >= DIAGNOSTIC_TOTAL_QUESTIONS) {
        await submitTest("The diagnostic was submitted after the final question.");
        return;
      }

      const nextQuestion = await getNextDiagnosticQuestion(session.id);
      if (!nextQuestion) {
        await submitTest("The adaptive engine completed the diagnostic and submitted your test.");
        return;
      }

      setQuestionIndex(nextIndex);
      setQuestionBank((current) => (nextQuestion ? [...current, nextQuestion] : current));
      setCurrentQuestion(nextQuestion);
      setQuestionStartedAt(Date.now());
    } catch {
      toast({
        title: "Unable to continue",
        description: "The next diagnostic step could not be loaded.",
        variant: "error",
      });
    }
  }, [
    currentQuestion,
    activeQuestionIndex,
    questionBank,
    questionStartedAt,
    selectedAnswer,
    session.id,
    setQuestionIndex,
    submitTest,
    toast,
    visibleQuestionIndex,
  ]);

  const handleSelectAnswer = useCallback(
    (value: string) => {
      if (!currentQuestion) {
        return;
      }
      const startedAt = answerStartedAtByQuestionId[currentQuestion.id] ?? questionStartedAt;
      setAnswersByQuestionId((current) => ({
        ...current,
        [currentQuestion.id]: value,
      }));
      setTimeTakenByQuestionId((current) => ({
        ...current,
        [currentQuestion.id]: Math.max(1, Math.round((Date.now() - startedAt) / 1000)),
      }));
    },
    [answerStartedAtByQuestionId, currentQuestion, questionStartedAt],
  );

  const goToQuestion = useCallback(
    (index: number) => {
      const nextQuestion = questionBank[index];
      if (!nextQuestion || fullscreenLocked) {
        return;
      }
      setCurrentQuestion(nextQuestion);
      setQuestionIndex(index + 1);
      setQuestionStartedAt(Date.now());
    },
    [fullscreenLocked, questionBank, setQuestionIndex],
  );

  return (
    <div className="diagnostic-shell min-h-screen text-slate-100">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
          className="diagnostic-glass p-6 sm:p-8"
        >
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-violet-300">Strict Diagnostic Mode</p>
              <h1 className="mt-3 max-w-4xl text-4xl font-semibold tracking-tight text-slate-50 sm:text-5xl">Python Track Diagnostic</h1>
              <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400">
                One question per screen. No copy, paste, tab switching, or pausing. The system will auto-submit on time expiry or repeated violations.
              </p>
            </div>
            <TimerComponent remainingSeconds={remainingSeconds} />
          </div>
        </motion.section>

        <div className="grid gap-6 xl:grid-cols-[300px_minmax(0,1fr)]">
          <aside className="space-y-4 xl:sticky xl:top-6 xl:self-start">
            <div className="diagnostic-glass-soft p-5">
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-violet-300">Palette</p>
                <span className="rounded-full bg-slate-950/70 px-3 py-1 text-xs text-slate-300">
                  {answeredCount}/{totalQuestions}
                </span>
              </div>
              <div className="diagnostic-progress-track mt-4 h-2 rounded-full">
                <motion.div
                  initial={false}
                  animate={{ width: `${progressPercent}%` }}
                  transition={{ duration: 0.35, ease: "easeOut" }}
                  className="diagnostic-progress-fill h-2 rounded-full"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <div className="mt-5 grid grid-cols-5 gap-2">
                {questionBank.map((question, index) => {
                  const isCurrent = question.id === currentQuestion?.id;
                  const isAnswered = Boolean((answersByQuestionId[question.id] ?? "").trim());
                  return (
                    <button
                      key={question.id}
                      type="button"
                      onClick={() => goToQuestion(index)}
                      disabled={fullscreenLocked}
                      className={[
                        "h-11 rounded-2xl border text-sm font-semibold transition",
                        isCurrent
                          ? "border-violet-300 bg-violet-500 text-white shadow-[0_12px_40px_-22px_rgba(139,92,246,0.9)]"
                          : isAnswered
                            ? "border-emerald-400/40 bg-emerald-500/15 text-emerald-100"
                            : "border-slate-700 bg-slate-950/70 text-slate-300 hover:border-slate-500",
                      ].join(" ")}
                      aria-label={`Go to question ${index + 1}`}
                    >
                      {index + 1}
                    </button>
                  );
                })}
              </div>
              <p className="mt-4 text-xs leading-5 text-slate-500">
                {lastSavedAt ? `Auto-saved ${lastSavedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : "Auto-save ready"}
              </p>
            </div>

            <div className="diagnostic-glass-soft p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-violet-300">Integrity Rules</p>
              <ul className="mt-4 space-y-3 text-sm text-slate-300">
                <li>Fullscreen required</li>
                <li>Tab/window blur is monitored</li>
                <li>No right click, copy, cut, or paste</li>
                <li>Answers auto-save locally</li>
              </ul>
            </div>

            {autoSubmittingReason ? (
              <div className="diagnostic-glass-soft border-amber-400/20 bg-amber-500/10 p-5 text-sm text-amber-100">
                {autoSubmittingReason}
              </div>
            ) : null}
          </aside>

          <div className="space-y-6">
            <AnimatePresence mode="wait">
              {currentQuestion ? (
                <QuestionCard
                  key={currentQuestion.id}
                  question={currentQuestion}
                  currentIndex={visibleQuestionIndex}
                  totalQuestions={totalQuestions}
                  selectedAnswer={selectedAnswer}
                  onSelectAnswer={handleSelectAnswer}
                />
              ) : (
                <motion.div
                  key="diagnostic-loading"
                  initial={{ opacity: 0, y: 18 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  className="diagnostic-glass p-8 text-center text-slate-300"
                >
                  Loading the next diagnostic question...
                </motion.div>
              )}
            </AnimatePresence>

            <div className="flex items-center justify-end gap-3">
              <Button
                onClick={() => goToQuestion(Math.max(0, activeQuestionIndex - 1))}
                disabled={activeQuestionIndex <= 0 || submitMutation.isPending || fullscreenLocked || !currentQuestion}
                className="border border-slate-700 bg-slate-950/70 text-slate-100 hover:bg-slate-900"
              >
                Previous
              </Button>
              <Button
                onClick={() => void handleAdvance()}
                disabled={!selectedAnswer || submitMutation.isPending || fullscreenLocked || !currentQuestion}
                className="diagnostic-button-primary min-w-[160px]"
              >
                {visibleQuestionIndex >= totalQuestions ? "Submit" : "Next"}
              </Button>
            </div>
          </div>
        </div>
      </div>

      <WarningModal
        open={Boolean(warning)}
        title={warning?.title ?? ""}
        description={warning?.description ?? ""}
        confirmLabel={warning?.blocking ? "Return to Fullscreen" : "Understood"}
        onConfirm={() => {
          if (warning?.blocking) {
            void requestFullscreen();
            return;
          }
          clearWarning();
        }}
        blocking={Boolean(warning?.blocking)}
      />
    </div>
  );
}
