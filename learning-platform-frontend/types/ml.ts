export type LearnerFeatureSnapshot = {
  user_id: number;
  tenant_id: number;
  learning_speed: number;
  retention_rate: number;
  topic_difficulty_score: number;
  user_engagement_score: number;
  total_learning_events: number;
  average_answer_accuracy: number;
  average_time_spent_minutes: number;
};

export type MLModelRecord = {
  id: number;
  tenant_id: number;
  model_name: string;
  version: string;
  model_type: string;
  metrics: Record<string, string | number>;
  artifact_uri: string;
  is_active: boolean;
  created_at: string;
};

export type MLTrainingRun = {
  id: number;
  tenant_id: number;
  model_name: string;
  status: string;
  trained_rows: number;
  metrics: Record<string, string | number>;
  created_at: string;
};

export type MLOutputOverview = {
  latest_feature_snapshot?: LearnerFeatureSnapshot | null;
  active_models: MLModelRecord[];
  recent_training_runs: MLTrainingRun[];
};
