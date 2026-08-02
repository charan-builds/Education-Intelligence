"use client";

import { create } from "zustand";

import { DIAGNOSTIC_TOTAL_QUESTIONS } from "@/features/diagnostic/config";

type WarningEvent = {
  id: number;
  title: string;
  description: string;
  blocking?: boolean;
};

type DiagnosticTestState = {
  selectedGoalId: number | null;
  selectedGoalName: string | null;
  selectedPath: string | null;
  testId: number | null;
  currentQuestionIndex: number;
  totalQuestions: number;
  tabSwitchCount: number;
  latestWarning: WarningEvent | null;
  setGoal: (goalId: number, goalName: string) => void;
  setPath: (pathId: string) => void;
  setTestSession: (testId: number) => void;
  setQuestionIndex: (index: number) => void;
  registerTabWarning: (warning: Omit<WarningEvent, "id">) => number;
  setWarning: (warning: Omit<WarningEvent, "id"> | null) => void;
  clearWarning: () => void;
  resetDiagnosticState: () => void;
};

const initialState = {
  selectedGoalId: null,
  selectedGoalName: null,
  selectedPath: null,
  testId: null,
  currentQuestionIndex: 1,
  totalQuestions: DIAGNOSTIC_TOTAL_QUESTIONS,
  tabSwitchCount: 0,
  latestWarning: null,
};

export const useDiagnosticTestStore = create<DiagnosticTestState>((set) => ({
  ...initialState,
  setGoal: (goalId, goalName) => set({ selectedGoalId: goalId, selectedGoalName: goalName }),
  setPath: (pathId) => set({ selectedPath: pathId }),
  setTestSession: (testId) => set({ testId }),
  setQuestionIndex: (index) => set({ currentQuestionIndex: index }),
  registerTabWarning: (warning) => {
    let nextCount = 0;
    set((state) => {
      nextCount = state.tabSwitchCount + 1;
      return {
        tabSwitchCount: nextCount,
        latestWarning: { ...warning, id: Date.now() },
      };
    });
    return nextCount;
  },
  setWarning: (warning) =>
    set({
      latestWarning: warning ? { ...warning, id: Date.now() } : null,
    }),
  clearWarning: () => set({ latestWarning: null }),
  resetDiagnosticState: () => set(initialState),
}));

