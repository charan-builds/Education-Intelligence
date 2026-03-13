"use client";

export const dynamic = "force-dynamic";

import { useMemo, useState } from "react";

import { startDiagnostic, submitAnswers } from "@/services/diagnosticService";
import type { DiagnosticAnswerPayload } from "@/types/diagnostic";

type Choice = {
  id: string;
  label: string;
  isCorrect: boolean;
};

type UiQuestion = {
  question_id: number;
  topic_id: number;
  prompt: string;
  choices: Choice[];
};

const QUESTION_SET: UiQuestion[] = [
  {
    question_id: 101,
    topic_id: 1,
    prompt: "Which Python library is commonly used for numerical arrays?",
    choices: [
      { id: "a", label: "NumPy", isCorrect: true },
      { id: "b", label: "Flask", isCorrect: false },
      { id: "c", label: "Django", isCorrect: false },
      { id: "d", label: "FastAPI", isCorrect: false },
    ],
  },
  {
    question_id: 102,
    topic_id: 2,
    prompt: "What does a high variance in a model typically indicate?",
    choices: [
      { id: "a", label: "Underfitting", isCorrect: false },
      { id: "b", label: "Overfitting", isCorrect: true },
      { id: "c", label: "Perfect generalization", isCorrect: false },
      { id: "d", label: "No training needed", isCorrect: false },
    ],
  },
  {
    question_id: 103,
    topic_id: 3,
    prompt: "Which concept is required before understanding gradient descent well?",
    choices: [
      { id: "a", label: "Video editing", isCorrect: false },
      { id: "b", label: "Basic calculus", isCorrect: true },
      { id: "c", label: "Network routing", isCorrect: false },
      { id: "d", label: "UI theming", isCorrect: false },
    ],
  },
];

export default function DiagnosticTestPage() {
  const [goalId, setGoalId] = useState<number>(1);
  const [testId, setTestId] = useState<number | null>(null);
  const [started, setStarted] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedChoice, setSelectedChoice] = useState<string | null>(null);
  const [answers, setAnswers] = useState<DiagnosticAnswerPayload[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [submitMessage, setSubmitMessage] = useState<string>("");
  const [error, setError] = useState<string>("");

  const currentQuestion = QUESTION_SET[currentIndex] ?? null;
  const progressPercent = useMemo(
    () => Math.round(((currentIndex + 1) / QUESTION_SET.length) * 100),
    [currentIndex],
  );

  async function handleStart(): Promise<void> {
    setError("");
    setSubmitMessage("");
    setIsStarting(true);
    try {
      const session = await startDiagnostic(goalId);
      setTestId(session.id);
      setStarted(true);
      setCurrentIndex(0);
      setAnswers([]);
      setSelectedChoice(null);
    } catch {
      setError("Failed to start diagnostic test.");
    } finally {
      setIsStarting(false);
    }
  }

  async function handleNext(): Promise<void> {
    if (!currentQuestion || !selectedChoice) {
      return;
    }

    const selected = currentQuestion.choices.find((choice) => choice.id === selectedChoice);
    if (!selected) {
      return;
    }

    const answerPayload: DiagnosticAnswerPayload = {
      question_id: currentQuestion.question_id,
      user_answer: selected.label,
      score: selected.isCorrect ? 100 : 0,
      time_taken: 15,
    };

    const nextAnswers = [...answers, answerPayload];
    setAnswers(nextAnswers);
    setSelectedChoice(null);

    const isLast = currentIndex === QUESTION_SET.length - 1;
    if (!isLast) {
      setCurrentIndex((prev) => prev + 1);
      return;
    }

    if (!testId) {
      setError("Missing test session id.");
      return;
    }

    setIsSubmitting(true);
    setError("");
    try {
      await submitAnswers(testId, nextAnswers);
      setSubmitMessage("Diagnostic submitted successfully.");
    } catch {
      setError("Failed to submit diagnostic answers.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-6 py-10">
      <h1 className="text-3xl font-semibold tracking-tight">Diagnostic Test</h1>
      <p className="mt-2 text-slate-600">Answer questions to evaluate your current knowledge level.</p>

      {!started ? (
        <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <label className="block text-sm font-medium text-slate-700" htmlFor="goalId">
            Goal ID
          </label>
          <input
            id="goalId"
            type="number"
            min={1}
            value={goalId}
            onChange={(event) => setGoalId(Number(event.target.value || 1))}
            className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
          />

          <button
            type="button"
            onClick={handleStart}
            disabled={isStarting}
            className="mt-4 rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isStarting ? "Starting..." : "Start Diagnostic"}
          </button>
        </section>
      ) : (
        <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5">
            <div className="mb-2 flex items-center justify-between text-sm text-slate-600">
              <span>
                Question {Math.min(currentIndex + 1, QUESTION_SET.length)} of {QUESTION_SET.length}
              </span>
              <span>{progressPercent}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-slate-200">
              <div
                className="h-2 rounded-full bg-brand-600 transition-all"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {currentQuestion && !submitMessage ? (
            <>
              <h2 className="text-xl font-medium text-slate-900">{currentQuestion.prompt}</h2>
              <div className="mt-4 space-y-3">
                {currentQuestion.choices.map((choice) => (
                  <label
                    key={choice.id}
                    className="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-200 px-4 py-3"
                  >
                    <input
                      type="radio"
                      name={`question-${currentQuestion.question_id}`}
                      checked={selectedChoice === choice.id}
                      onChange={() => setSelectedChoice(choice.id)}
                      className="h-4 w-4"
                    />
                    <span className="text-slate-800">{choice.label}</span>
                  </label>
                ))}
              </div>

              <button
                type="button"
                onClick={handleNext}
                disabled={!selectedChoice || isSubmitting}
                className="mt-6 rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSubmitting ? "Submitting..." : currentIndex === QUESTION_SET.length - 1 ? "Submit" : "Next Question"}
              </button>
            </>
          ) : (
            <p className="text-emerald-700">{submitMessage}</p>
          )}
        </section>
      )}

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
    </main>
  );
}
