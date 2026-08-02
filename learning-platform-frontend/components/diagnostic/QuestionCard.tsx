"use client";

import { motion } from "framer-motion";

import type { DiagnosticOption, DiagnosticQuestion } from "@/types/diagnostic";

type Props = {
  question: DiagnosticQuestion;
  currentIndex: number;
  totalQuestions: number;
  selectedAnswer: string;
  onSelectAnswer: (value: string) => void;
};

function badgeTone(label: string) {
  const normalized = label.toLowerCase();
  if (normalized === "hard") {
    return "bg-rose-500/15 text-rose-200 ring-rose-400/30";
  }
  if (normalized === "medium") {
    return "bg-amber-500/15 text-amber-200 ring-amber-400/30";
  }
  return "bg-emerald-500/15 text-emerald-200 ring-emerald-400/30";
}

function normalizeOption(option: DiagnosticOption | string, index: number): DiagnosticOption {
  if (typeof option === "string") {
    return { key: String.fromCharCode(65 + index), text: option };
  }
  return option;
}

function difficultyText(question: DiagnosticQuestion) {
  if (question.difficulty_label) {
    return question.difficulty_label;
  }
  if (question.difficulty_level === 1 || question.difficulty === 1) {
    return "easy";
  }
  if (question.difficulty_level === 3 || question.difficulty === 3) {
    return "hard";
  }
  return "medium";
}

export default function QuestionCard({
  question,
  currentIndex,
  totalQuestions,
  selectedAnswer,
  onSelectAnswer,
}: Props) {
  const conceptTag = question.concept_tag ?? `topic-${question.topic_id}`;
  const answerOptions = (question.answer_options?.length ? question.answer_options : question.options ?? []).map(
    normalizeOption,
  );
  const isMultipleChoice = ["multiple_choice", "mcq"].includes(question.question_type);
  const difficultyLabel = difficultyText(question);

  return (
    <motion.div
      key={question.id}
      initial={{ opacity: 0, y: 18, scale: 0.985 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="diagnostic-glass p-6 sm:p-8"
    >
      <div className="flex flex-col gap-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm font-medium text-slate-400">
            Question {currentIndex}/{totalQuestions}
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ${badgeTone(difficultyLabel)}`}>
              {difficultyLabel}
            </span>
            <span className="inline-flex rounded-full bg-violet-500/15 px-3 py-1 text-xs font-semibold text-violet-200 ring-1 ring-violet-400/30">
              {conceptTag}
            </span>
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Focus Question</p>
          <h2 className="max-w-4xl text-2xl font-semibold leading-10 text-slate-50 sm:text-3xl">
            {question.question_text}
          </h2>
        </div>

        {isMultipleChoice && answerOptions.length > 0 ? (
          <div className="grid gap-4">
            {answerOptions.map((option, index) => {
              const isSelected = selectedAnswer === option.text;
              return (
                <button
                  key={`${option.key}-${option.text}`}
                  type="button"
                  onClick={() => onSelectAnswer(option.text)}
                  className={[
                    "group flex items-start gap-4 rounded-[24px] border px-5 py-4 text-left transition duration-200",
                    isSelected
                      ? "border-violet-400/70 bg-violet-500/12 shadow-[0_18px_60px_-30px_rgba(124,58,237,0.65)]"
                      : "border-slate-700/70 bg-slate-900/55 hover:border-slate-500/80 hover:bg-slate-900/80",
                  ].join(" ")}
                >
                  <span
                    className={[
                      "mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border text-sm font-bold",
                      isSelected
                        ? "border-violet-400 bg-violet-500 text-white"
                        : "border-slate-700 bg-slate-950 text-slate-300",
                    ].join(" ")}
                  >
                    {option.key || String.fromCharCode(65 + index)}
                  </span>
                  <div className="flex-1">
                    <p className="text-base font-medium text-slate-100">{option.text}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {isSelected ? "Selected answer" : "Single choice only"}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="rounded-[24px] border border-slate-800 bg-slate-900/70 p-4">
            <p className="mb-3 text-sm font-medium text-slate-300">Write your answer</p>
            <textarea
              value={selectedAnswer}
              onChange={(event) => onSelectAnswer(event.target.value)}
              className="min-h-36 w-full rounded-[20px] border border-slate-700 bg-slate-950/85 px-4 py-3 text-sm leading-7 text-slate-100 outline-none transition focus:border-violet-400 focus:ring-4 focus:ring-violet-500/10"
              placeholder="Type your response here"
            />
          </div>
        )}
      </div>
    </motion.div>
  );
}
