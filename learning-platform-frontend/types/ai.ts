export type AIChatHistoryItem = {
  request_id: string;
  role: string;
  message: string;
  response: string | null;
  status: string;
  created_at: string;
};

export type AIChatRequest = {
  message: string;
  chat_history?: { role: string; content: string }[];
};

export type AIChatResponse = {
  request_id: string;
  reply: string;
  advisor_type: string;
  used_ai: boolean;
  suggested_focus_topics: number[];
  why_recommended: string[];
  provider: string | null;
  next_checkin_date: string | null;
  session_summary: string;
  memory_summary: Record<string, unknown>;
  prompt_context: Record<string, unknown>;
  history: AIChatHistoryItem[];
};
