export type MentorChatRequest = {
  message: string;
  user_id: number;
  tenant_id: number;
  chat_history?: { role: string; content: string }[];
  request_id?: string;
};

export type MentorChatResponse = {
  reply: string;
  advisor_type: string;
  used_ai: boolean;
  suggested_focus_topics: number[];
  why_recommended?: string[];
  provider?: string | null;
  next_checkin_date: string | null;
  session_summary?: string;
};

export type MentorSuggestionsResponse = {
  suggestions: string[];
};

export type MentorProgressWeek = {
  week: string;
  completion_percent: number;
};

export type MentorProgressAnalysisResponse = {
  topic_improvements: Record<number, number>;
  weekly_progress: MentorProgressWeek[];
  recommended_focus: string[];
};

export type MentorNotificationItem = {
  trigger: string;
  severity: "low" | "medium" | "high" | string;
  title: string;
  message: string;
};

export type MentorNotificationsResponse = {
  notifications: MentorNotificationItem[];
};

export type AgentObservedState = {
  roadmap_id?: number | null;
  completion_percent: number;
  focus_score: number;
  streak_days: number;
  xp: number;
  risk_level: string;
  weak_topics: { topic_id: number; topic_name: string; score: number }[];
  due_reviews: { topic_id?: number; topic_name?: string }[];
  next_pending_topic?: { topic_id: number; topic_name: string; priority: number } | null;
  active_topic_count: number;
  completed_topic_count: number;
  last_activity?: Record<string, unknown> | null;
  memory_summary: {
    learner_summary?: string;
    weak_topics?: string[];
    strong_topics?: string[];
    preferred_learning_style?: string;
    learning_speed?: number;
    recent_session_summaries?: string[];
  };
  notification_candidates: MentorNotificationItem[];
};

export type AgentDecision = {
  decision_type: string;
  priority: string;
  confidence: number;
  topic_id?: number | null;
  title: string;
  why: string;
};

export type AgentAction = {
  action_type: string;
  status: string;
  title: string;
  details: Record<string, unknown>;
  why: string;
};

export type AutonomousAgentResponse = {
  agent_mode: string;
  observed_state: AgentObservedState;
  decisions: AgentDecision[];
  actions: AgentAction[];
  notifications: MentorNotificationItem[];
  memory_summary: AgentObservedState["memory_summary"];
  next_best_topic_id?: number | null;
  cycle_summary: string;
};
