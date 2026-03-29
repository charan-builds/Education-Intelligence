export type MentorChatRequest = {
  message: string;
  user_id: number;
  tenant_id: number;
  chat_history?: { role: string; content: string }[];
  request_id?: string;
};

export type MentorChatResponse = {
  request_id?: string | null;
  status?: string;
  reply: string;
  advisor_type: string;
  used_ai: boolean;
  suggested_focus_topics: number[];
  why_recommended?: string[];
  provider?: string | null;
  next_checkin_date: string | null;
  session_summary?: string;
};

export type MentorChatStatusResponse = {
  request_id: string;
  status: string;
  channel: string;
  reply?: string | null;
  delivered: boolean;
  acked: boolean;
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

export type MentorLearner = {
  user_id: number;
  email: string;
  display_name: string;
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

export type HybridMentorMatch = {
  mentor_id: number;
  display_name: string;
  email: string;
  role: string;
  match_score: number;
  availability: string;
  specialties: string[];
  reasons: string[];
  ai_handoff_summary: string;
};

export type HybridLearnerProfile = {
  user_id: number;
  tenant_id: number;
  completion_rate: number;
  learning_style: string;
  session_intensity: string;
  weak_topics: string[];
  strong_topics: string[];
  human_support_needed: boolean;
  summary: string;
};

export type HybridCollaborationBrief = {
  session_goal: string;
  ai_role: string;
  human_role: string;
  shared_context: string[];
  handoff_notes: string[];
  escalation_triggers: string[];
};

export type HybridSupportChannel = {
  channel_type: string;
  title: string;
  description: string;
  href: string;
  realtime_enabled: boolean;
  why: string;
};

export type HybridMentorshipOverview = {
  learner_profile: HybridLearnerProfile;
  mentor_matches: HybridMentorMatch[];
  collaboration_brief: HybridCollaborationBrief;
  live_support_channels: HybridSupportChannel[];
};

export type HybridSessionPlanRequest = {
  learner_id?: number | null;
  mentor_id?: number | null;
  topic_id?: number | null;
};

export type HybridSessionPlanResponse = {
  mentor_id?: number | null;
  mentor_name: string;
  session_title: string;
  agenda: string[];
  ai_prep_notes: string[];
  mentor_focus: string[];
  follow_up_actions: string[];
};
