export type DiagnosticOption = {
  key: string;
  text: string;
};

export type DiagnosticAnswerPayload = {
  question_id: number;
  user_answer: string;
  score?: number | null;
  time_taken: number;
};

export type DiagnosticSubmitAnswerPayload = {
  question_id: number;
  selected_answer: string;
  time_taken: number;
};

export type DiagnosticQuestion = {
  test_id: number;
  id: number;
  topic_id: number;
  difficulty_level: number;
  difficulty_label: "easy" | "medium" | "hard" | string;
  difficulty?: number | string;
  concept_tag?: string | null;
  question_type: "multiple_choice" | "short_text" | string;
  question_text: string;
  answer_options?: string[];
  options?: Array<DiagnosticOption | string>;
};

export type DiagnosticSubmittedAnswer = {
  question_id: number;
  selected_answer: string;
  score: number;
  time_taken: number;
  difficulty_level: number;
  difficulty_label: "easy" | "medium" | "hard" | string;
};

export type DiagnosticSession = {
  id: number;
  user_id: number;
  goal_id: number;
  started_at: string;
  completed_at: string | null;
  answered_count?: number;
  total_score?: number;
  percentage_score?: number;
  questions?: DiagnosticQuestion[];
  answers?: DiagnosticSubmittedAnswer[];
  adaptive_summary?: {
    topic_levels: Array<{
      topic_id: number;
      level: string;
      average_accuracy: number;
      average_time_taken: number;
      average_attempts: number;
      recommended_difficulty: number;
    }>;
  };
};

export type DiagnosticAnswerResponse = {
  test_id: number;
  question_id: number;
  answered_count: number;
  completed_at: string | null;
  adaptive_decision?: {
    topic_id: number;
    current_difficulty: number;
    recommended_difficulty: number;
    accuracy: number;
    time_taken: number;
    attempt_count: number;
    level: string;
    rule: string;
  } | null;
};

export type DiagnosticResult = {
  test_id: number;
  topic_scores: Record<number, number>;
  weak_topic_ids: number[];
  foundation_gap_topic_ids: number[];
  recommendation_levels: Record<number, string>;
  roadmap: Roadmap | null;
};
import type { Roadmap } from "@/types/roadmap";
