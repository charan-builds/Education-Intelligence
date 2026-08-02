"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";

import DiagnosticIntroPage from "@/components/diagnostic/DiagnosticIntroPage";
import GoalSelectionPage from "@/components/diagnostic/GoalSelectionPage";
import TestScreen from "@/components/diagnostic/TestScreen";
import { useToast } from "@/components/providers/ToastProvider";
import { DIAGNOSTIC_TRACK_ID } from "@/features/diagnostic/config";
import { getDiagnosticSession, getNextDiagnosticQuestion, startDiagnostic } from "@/services/diagnosticService";
import { getGoals, selectCurrentGoal } from "@/services/goalService";
import { useAuth } from "@/hooks/useAuth";
import { useDiagnosticTestStore } from "@/stores/useDiagnosticTestStore";
import type { Goal } from "@/types/goal";
import { getLearnerRoutes } from "@/utils/appRoutes";

export default function StudentDiagnosticPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { role, user } = useAuth();
  const learnerRoutes = getLearnerRoutes(role);
  const { toast } = useToast();
  const selectedGoalId = useDiagnosticTestStore((state) => state.selectedGoalId);
  const selectedGoalName = useDiagnosticTestStore((state) => state.selectedGoalName);
  const selectedPath = useDiagnosticTestStore((state) => state.selectedPath);
  const setGoal = useDiagnosticTestStore((state) => state.setGoal);
  const setPath = useDiagnosticTestStore((state) => state.setPath);
  const setTestSession = useDiagnosticTestStore((state) => state.setTestSession);
  const setQuestionIndex = useDiagnosticTestStore((state) => state.setQuestionIndex);
  const [setupStep, setSetupStep] = useState<"goal" | "intro">("goal");

  const testId = Number(searchParams.get("test_id") ?? "");
  const goalIdFromQuery = Number(searchParams.get("goal_id") ?? "");
  const isTestMode = Number.isFinite(testId) && testId > 0 && Number.isFinite(goalIdFromQuery) && goalIdFromQuery > 0;

  const goalsQuery = useQuery({
    queryKey: ["diagnostic", "setup", "goals"],
    queryFn: getGoals,
    enabled: !isTestMode,
  });

  const sessionQuery = useQuery({
    queryKey: ["diagnostic", "session", testId],
    queryFn: () => getDiagnosticSession(testId),
    enabled: isTestMode,
  });

  const firstQuestionQuery = useQuery({
    queryKey: ["diagnostic", "first-question", testId],
    queryFn: () => getNextDiagnosticQuestion(testId),
    enabled: isTestMode,
  });

  const startMutation = useMutation({
    mutationFn: async (goalId: number) => {
      await selectCurrentGoal(goalId);
      return startDiagnostic(goalId, user?.user_id);
    },
    onSuccess: (session, goalId) => {
      setTestSession(session.id);
      setQuestionIndex(1);
      router.push(`${learnerRoutes.diagnostic}?goal_id=${goalId}&test_id=${session.id}`);
    },
    onError: () => {
      toast({
        title: "Diagnostic could not start",
        description: "The diagnostic start request failed. Check your goal and session state.",
        variant: "error",
      });
    },
  });

  useEffect(() => {
    if (!isTestMode && goalIdFromQuery > 0 && goalsQuery.data?.items?.length) {
      const goal = goalsQuery.data.items.find((item) => item.id === goalIdFromQuery);
      if (goal) {
        setGoal(goal.id, goal.name);
      }
    }
  }, [goalIdFromQuery, goalsQuery.data?.items, isTestMode, setGoal]);

  const goals = useMemo(() => goalsQuery.data?.items ?? [], [goalsQuery.data?.items]);
  const recommendedGoal = useMemo(
    () => goals.find((goal) => goal.name.toLowerCase().includes("ai") || goal.name.toLowerCase().includes("ml")) ?? goals[0] ?? null,
    [goals],
  );

  useEffect(() => {
    if (!selectedGoalId && recommendedGoal) {
      setGoal(recommendedGoal.id, recommendedGoal.name);
    }
  }, [recommendedGoal, selectedGoalId, setGoal]);

  useEffect(() => {
    if (!isTestMode) {
      return;
    }
    if (sessionQuery.data?.completed_at || (sessionQuery.isSuccess && firstQuestionQuery.isSuccess && firstQuestionQuery.data === null)) {
      router.replace(`${learnerRoutes.diagnosticResult}?test_id=${testId}`);
    }
  }, [
    firstQuestionQuery.data,
    firstQuestionQuery.isSuccess,
    isTestMode,
    learnerRoutes.diagnosticResult,
    router,
    sessionQuery.data?.completed_at,
    sessionQuery.isSuccess,
    testId,
  ]);

  async function handleStartDiagnostic() {
    if (!selectedGoalId) {
      return;
    }
    await startMutation.mutateAsync(selectedGoalId);
  }

  if (isTestMode) {
    if (sessionQuery.isLoading || firstQuestionQuery.isLoading) {
      return (
        <div className="min-h-screen bg-[linear-gradient(180deg,#020617_0%,#0f172a_36%,#111827_100%)] px-4 py-10 text-slate-100">
          <div className="mx-auto max-w-5xl rounded-[32px] border border-slate-800 bg-[#111827] p-8">
            Loading strict diagnostic environment...
          </div>
        </div>
      );
    }

    if (sessionQuery.isError || !sessionQuery.data) {
      return (
        <div className="min-h-screen bg-[linear-gradient(180deg,#020617_0%,#0f172a_36%,#111827_100%)] px-4 py-10 text-slate-100">
          <div className="mx-auto max-w-5xl rounded-[32px] border border-slate-800 bg-[#111827] p-8">
            Unable to load the diagnostic session.
          </div>
        </div>
      );
    }

    return <TestScreen session={sessionQuery.data} initialQuestion={firstQuestionQuery.data ?? null} role={role} />;
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#020617_0%,#0f172a_36%,#111827_100%)] text-slate-100">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <section className="rounded-[32px] border border-slate-800 bg-[#0f172a] p-6 shadow-[0_24px_80px_-20px_rgba(0,0,0,0.55)] sm:p-8">
          <div className="space-y-4">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-violet-300">Learning Intelligence Platform</p>
            <h1 className="text-4xl font-semibold text-slate-50 sm:text-5xl">Focused Diagnostic Test System</h1>
            <p className="max-w-4xl text-sm leading-7 text-slate-400">
              This diagnostic is built to find knowledge gaps, lock the learner into the Python track, and generate a roadmap toward AI/ML engineering without distractions.
            </p>
          </div>
        </section>

        {setupStep === "goal" ? (
          <GoalSelectionPage
            goals={goals}
            selectedGoalId={selectedGoalId}
            onSelectGoal={(goal: Goal) => setGoal(goal.id, goal.name)}
            onContinue={() => setSetupStep("intro")}
            isBusy={goalsQuery.isLoading}
          />
        ) : (
          <DiagnosticIntroPage
            selectedGoalName={selectedGoalName}
            selectedPath={selectedPath}
            onSelectPath={() => setPath(DIAGNOSTIC_TRACK_ID)}
            onStart={() => void handleStartDiagnostic()}
            isStarting={startMutation.isPending}
          />
        )}
      </div>
    </div>
  );
}
