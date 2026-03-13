export type DiagnosticAnswerPayload = {
  question_id: number;
  user_answer: string;
  score: number;
  time_taken: number;
};

export type DiagnosticSession = {
  id: number;
  user_id: number;
  goal_id: number;
  started_at: string;
  completed_at: string | null;
};

export type DiagnosticResult = {
  test_id: number;
  topic_scores: Record<number, number>;
};
