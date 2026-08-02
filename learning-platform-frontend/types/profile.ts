export type ExperienceLevel = "beginner" | "intermediate" | "advanced";
export type DailyStudyTime =
  | "less_than_30_min"
  | "30_to_60_min"
  | "1_to_2_hours"
  | "2_to_4_hours"
  | "4_plus_hours";
export type LearningStyle = "visual" | "reading" | "hands_on" | "video" | "mixed";
export type TargetTimeline = "1_month" | "3_months" | "6_months" | "12_months" | "flexible";

export type UserProfile = {
  user_id: number;
  full_name?: string | null;
  profile_photo_url?: string | null;
  bio?: string | null;
  college_name?: string | null;
  degree?: string | null;
  year_of_study?: number | null;
  github_url?: string | null;
  github_repo_count?: number | null;
  github_languages?: string[] | null;
  github_activity_score?: number | null;
  leetcode_url?: string | null;
  hackerrank_url?: string | null;
  linkedin_url?: string | null;
  experience_level?: ExperienceLevel | null;
  daily_study_time?: DailyStudyTime | null;
  learning_style?: LearningStyle | null;
  learning_goal_note?: string | null;
  target_timeline?: TargetTimeline | null;
  profile_completed: boolean;
};

export type UserProfileStatus = {
  user_id: number;
  profile_completed: boolean;
  required_fields_completed: boolean;
  missing_required_fields: string[];
};

export type UserProfileProgress = {
  completion_percent: number;
  missing_fields: string[];
};

export type OnboardingEventType = "step_start" | "step_completion" | "drop_off";

export type OnboardingEventPayload = {
  step_name: string;
  event_type: OnboardingEventType;
  metadata?: Record<string, unknown>;
};

export type UserProfilePayload = {
  full_name?: string | null;
  profile_photo_url?: string | null;
  bio?: string | null;
  college_name?: string | null;
  degree?: string | null;
  year_of_study?: number | null;
  github_url?: string | null;
  leetcode_url?: string | null;
  hackerrank_url?: string | null;
  linkedin_url?: string | null;
  experience_level?: ExperienceLevel | null;
  daily_study_time?: DailyStudyTime | null;
  learning_style?: LearningStyle | null;
  learning_goal_note?: string | null;
  target_timeline?: TargetTimeline | null;
  profile_completed?: boolean | null;
};
