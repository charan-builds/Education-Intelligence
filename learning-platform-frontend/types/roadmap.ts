export type RoadmapStep = {
  id: number;
  topic_id: number;
  phase?: string | null;
  estimated_time_hours: number;
  difficulty: string;
  priority: number;
  deadline: string;
  progress_status: string;
};

export type UpdateRoadmapStepPayload = {
  progress_status: "pending" | "in_progress" | "completed";
};

export type Roadmap = {
  id: number;
  user_id: number;
  goal_id: number;
  test_id: number;
  status: "generating" | "ready" | "failed" | string;
  error_message?: string | null;
  generated_at: string;
  steps: RoadmapStep[];
};

export type RoadmapPageMeta = {
  total: number;
  limit: number;
  offset: number;
  next_offset: number | null;
  next_cursor: string | null;
};

export type RoadmapPageResponse = {
  items: Roadmap[];
  meta: RoadmapPageMeta;
};
