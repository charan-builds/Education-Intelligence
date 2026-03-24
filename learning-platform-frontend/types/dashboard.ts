export type DashboardVelocityPoint = {
  label: string;
  minutes: number;
  completed_steps: number;
};

export type WeakTopicHeatmapItem = {
  topic_id: number;
  topic_name: string;
  score: number;
  mastery_delta: number;
  confidence: number;
};

export type MentorSuggestionCard = {
  id: number;
  title: string;
  message: string;
  why: string;
  topic_id: number | null;
  is_ai_generated: boolean;
};

export type SkillGraphNode = {
  topic_id: number;
  topic_name: string;
  status: string;
  dependencies: number[];
};

export type BadgeCard = {
  name: string;
  description: string;
  awarded_at: string;
};

export type LeaderboardEntry = {
  rank: number;
  user_id: number;
  name: string;
  xp: number;
  is_current_user: boolean;
};

export type StudentDashboardPayload = {
  tenant_id: number;
  user_id: number;
  completion_percent: number;
  streak_days: number;
  focus_score: number;
  xp: number;
  roadmap_progress: {
    total_steps: number;
    completed_steps: number;
    in_progress_steps: number;
    completion_percent: number;
  };
  learning_velocity: DashboardVelocityPoint[];
  weak_topic_heatmap: WeakTopicHeatmapItem[];
  weak_topics: WeakTopicHeatmapItem[];
  mentor_suggestions: MentorSuggestionCard[];
  retention: {
    tenant_id: number;
    user_id: number;
    average_retention_score: number;
    due_reviews: Array<{
      topic_id: number;
      topic_name: string;
      score: number;
      retention_score: number;
      review_interval_days: number;
      review_due_at: string | null;
      is_due: boolean;
    }>;
    upcoming_reviews: Array<{
      topic_id: number;
      topic_name: string;
      score: number;
      retention_score: number;
      review_interval_days: number;
      review_due_at: string | null;
      is_due: boolean;
    }>;
    recommended_resources: Array<{
      id: number;
      topic_id: number;
      topic_name: string;
      title: string;
      resource_type: string;
      difficulty: string;
      rating: number;
      url: string;
    }>;
  };
  skill_graph: SkillGraphNode[];
  gamification: {
    badges: BadgeCard[];
    leaderboard: LeaderboardEntry[];
  };
  recent_activity: Array<{
    event_type: string;
    created_at: string;
    topic_id: number | null;
  }>;
};

export type TeacherStudentRiskRow = {
  user_id: number;
  name: string;
  email: string;
  completion_percent: number;
  average_score: number;
  risk_level: string;
  xp: number;
};

export type TeacherDashboardPayload = {
  tenant_id: number;
  student_count: number;
  weak_topic_clusters: Array<{
    topic_id: number;
    topic_name: string;
    average_score: number;
    student_count: number;
  }>;
  performance_distribution: {
    critical: number;
    watch: number;
    strong: number;
  };
  top_students: TeacherStudentRiskRow[];
  bottom_students: TeacherStudentRiskRow[];
  risk_students: TeacherStudentRiskRow[];
};
