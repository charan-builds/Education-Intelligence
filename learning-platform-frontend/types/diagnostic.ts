export type DiagnosticAnswerPayload = {
  question_id: number;
  user_answer: string;
  score?: number | null;
  time_taken: number;
};

export type DiagnosticQuestion = {
  test_id: number;
  id: number;
  topic_id: number;
  difficulty: number;
  difficulty_label: string;
  question_type: "multiple_choice" | "short_text" | string;
  question_text: string;
  answer_options: string[];
};

export type DiagnosticSession = {
  id: number;
  user_id: number;
  goal_id: number;
  started_at: string;
  completed_at: string | null;
  answered_count?: number;
};

export type DiagnosticAnswerResponse = {
  test_id: number;
  question_id: number;
  answered_count: number;
  completed_at: string | null;
};

export type DiagnosticResult = {
  test_id: number;
  topic_scores: Record<number, number>;
  roadmap: Roadmap | null;
};
import type { Roadmap } from "@/types/roadmap";
