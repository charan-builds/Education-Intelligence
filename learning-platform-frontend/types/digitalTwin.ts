export type TwinTopicSignal = {
  topic_id: number;
  topic_name: string;
  score: number;
  retention_score?: number | null;
};

export type DigitalTwin = {
  user_id: number;
  tenant_id: number;
  current_model: {
    learner_summary: string;
    strengths: TwinTopicSignal[];
    weaknesses: TwinTopicSignal[];
    learning_speed: number;
    memory_retention: number;
    behavior_patterns: {
      average_session_minutes: number;
      study_event_count: number;
      cadence_pattern: string;
      engagement_pattern: string;
      profile_type: string;
      confidence: number;
      consistency: number;
      stamina: number;
    };
    roadmap_state: {
      total_steps: number;
      completed_steps: number;
      completion_percent: number;
    };
    retention_summary: {
      average_retention_score: number;
      due_reviews: Array<{ topic_name: string; retention_score: number }>;
    };
    twin_confidence: number;
  };
  predictions: {
    risk_prediction: {
      risk_score: number;
      risk_level: string;
      recommended_interventions: string[];
    };
    baseline: {
      strategy: string;
      daily_study_hours: number;
      estimated_completion_date: string;
      progress_curve: Array<{ day: number; date: string; hours_completed: number; progress_percent: number }>;
    };
    accelerated_focus: {
      strategy: string;
      daily_study_hours: number;
      estimated_completion_date: string;
      progress_curve: Array<{ day: number; date: string; hours_completed: number; progress_percent: number }>;
    };
    retention_first: {
      strategy: string;
      daily_study_hours: number;
      estimated_completion_date: string;
      progress_curve: Array<{ day: number; date: string; hours_completed: number; progress_percent: number }>;
    };
  };
  decision_support: {
    recommended_strategy: {
      strategy: string;
      summary: string;
      predicted_completion_date: string;
      predicted_readiness_percent: number;
      predicted_retention_percent: number;
      tradeoff: string;
    };
    strategy_comparison: Array<{
      strategy: string;
      summary: string;
      predicted_completion_date: string;
      predicted_readiness_percent: number;
      predicted_retention_percent: number;
      tradeoff: string;
    }>;
    recommended_learning_path: string[];
    why: string[];
  };
};
