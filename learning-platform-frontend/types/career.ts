export type CareerRoleMatch = {
  role_id: number;
  role_name: string;
  category: string;
  readiness_percent: number;
  matched_skills: string[];
  missing_skills: string[];
};

export type JobReadiness = {
  user_id: number;
  tenant_id: number;
  readiness_percent: number;
  confidence_label: string;
  breakdown: Record<string, number>;
  top_role_matches: CareerRoleMatch[];
  alternative_paths: CareerRoleMatch[];
};

export type ResumePreview = {
  headline: string;
  summary: string;
  skills: string[];
  projects: string[];
  achievements: string[];
};

export type InterviewQuestion = {
  question_type: string;
  question_text: string;
  answer_options: string[];
  correct_answer: string;
  explanation: string;
};

export type InterviewPrep = {
  role_name: string;
  mock_interview_prompt: string;
  questions: InterviewQuestion[];
};

export type CareerOverview = {
  readiness: JobReadiness;
  resume_preview: ResumePreview;
  career_path: {
    goal: string;
    estimated_duration_months: number;
    career_roadmap: Record<string, { duration_months: number; focus_areas: string[] }>;
  };
};
